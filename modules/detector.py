import json, time, socket
from datetime import datetime
from .http_utils import parse_status_and_headers, normalize_target
from .probes import followup_get, tecl_top, clte_top

def _send(sock, data):
    sock.sendall(data.encode('latin-1', 'ignore'))

def _recv_all(sock, timeout=2, chunk=4096):
    sock.settimeout(timeout)
    data = b""
    while True:
        try:
            part = sock.recv(chunk)
            if not part:
                break
            data += part
        except socket.timeout:
            break
    return data

def _probe_pair(host, port, top_builder):
    # open one socket, send top payload then follow-up on same socket
    res = {"top": {}, "follow": {}}
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(10)
    s.connect((host, port))
    t0 = time.time()
    _send(s, top_builder(f"{host}:{port}"))
    top_resp = _recv_all(s)
    t1 = time.time()

    res["top"]["latency_ms"] = int((t1 - t0) * 1000)
    res["top"]["raw_len"] = len(top_resp)
    status_top, hdrs_top = parse_status_and_headers(top_resp)
    res["top"]["status"] = status_top
    res["top"]["connection"] = ",".join(hdrs_top.get("connection", []))

    # follow-up
    _send(s, followup_get(f"{host}:{port}"))
    t2 = time.time()
    follow_resp = _recv_all(s)
    t3 = time.time()
    s.close()

    res["follow"]["latency_ms"] = int((t3 - t2) * 1000)
    res["follow"]["raw_len"] = len(follow_resp)
    status_f, hdrs_f = parse_status_and_headers(follow_resp)
    res["follow"]["status"] = status_f
    res["follow"]["connection"] = ",".join(hdrs_f.get("connection", []))
    res["follow"]["badreq"] = (status_f == 400)
    return res

def _score(result):
    score = 0
    # top 2xx/3xx but follow-up 400 => classic indicator
    if result["top"]["status"] and 200 <= result["top"]["status"] < 400 and result["follow"]["badreq"]:
        score += 40
    # big latency gap on follow-up (likely consumed)
    if result["follow"]["latency_ms"] >= 1500 and result["top"]["latency_ms"] < 800:
        score += 25
    # tiny or empty follow-up body
    if result["follow"]["raw_len"] < 120:
        score += 10
    # connection header contradictory / closed after KA
    if "keep-alive" in (result["top"]["connection"] or "").lower() and result["follow"]["raw_len"] == 0:
        score += 10
    return min(score, 100)

def auto_detect(target, outdir="loot"):
    host, port = normalize_target(target)
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    results = {
        "target": f"{host}:{port}",
        "ts": stamp,
        "tecl": _probe_pair(host, port, tecl_top),
        "clte": _probe_pair(host, port, clte_top),
    }
    results["tecl_score"] = _score(results["tecl"])
    results["clte_score"] = _score(results["clte"])
    verdict = max(results["tecl_score"], results["clte_score"])
    results["verdict_score"] = verdict
    results["verdict"] = "LIKELY" if verdict >= 80 else ("POSSIBLE" if verdict >= 50 else "UNLIKELY")

    # save
    import os
    os.makedirs(outdir, exist_ok=True)
    jpath = f"{outdir}/auto_detect_{host}_{port}_{stamp}.json"
    tpath = f"{outdir}/auto_detect_{host}_{port}_{stamp}.txt"
    with open(jpath, "w") as jf:
        json.dump(results, jf, indent=2)
    with open(tpath, "w") as tf:
        tf.write(f"Auto-detect @ {host}:{port}\n")
        for k in ("tecl_score","clte_score","verdict","verdict_score"):
            tf.write(f"{k}: {results[k]}\n")
        tf.write("\nTE.CL pair:\n")
        tf.write(json.dumps(results["tecl"], indent=2))
        tf.write("\n\nCL.TE pair:\n")
        tf.write(json.dumps(results["clte"], indent=2))
    print(f"[+] Auto-detect: {results['verdict']} ({results['verdict_score']})")
    print(f"[+] Saved: {jpath}\n    and {tpath}")
    return results
