# HTTP Smuggler — Desync Recon & Exploitation

HTTP Smuggler is a focused HTTP/1.1 request-smuggling reconnaissance and exploitation tool for advanced operators. It sends **raw**, hand-crafted HTTP/1.1 requests over plain TCP using sockets—no HTTP client libraries, no HTTPS, no Burp. It’s designed for environments where **frontend reverse proxies** multiplex user traffic to **origin servers** over **upstream HTTP/1.1** and ambiguities in request framing can be abused to create a **desynchronization (desync)** between the two.

![Screenshot_2025-08-07_12_53_58](https://github.com/user-attachments/assets/e8da1e81-8c2b-4c04-b257-8a48e657012a)

The tool bundles three core building blocks and four menu workflows:

* **Scanner** — quick TE.CL / CL.TE desync probes.
* **Payload Generator** — build reusable smuggle payloads (TE.CL login injection, CL.TE cache poison, or fully custom).
* **Executor** — send saved payloads verbatim, optionally followed by a second request on the **same socket** to confirm desync effects.
* **Auto-Detect (Scored)** — run structured probes and assign a desync likelihood score.
* **Auto-Exploit Chain** — pivot a confirmed vector into cache-poison or login-hijack automatically.
* **Full Chain** — detect → craft payload → execute proof → write report, in one pass.

> Scope: **HTTP only**. No TLS. The point is unmediated control over framing (`Content-Length`, `Transfer-Encoding`, body). Use your own TCP egress controls and OPSEC.

---

## Why HTTP Smuggling Still Matters

The danger zone is rarely the browser→edge TLS link. It’s **inside infrastructure** where **HTTP/1.1** still rides between devices.

### Reverse proxy → origin server links

* Client may use HTTPS, but the edge often talks to the origin over **raw HTTP/1.1**.
* That upstream hop is where parsing ambiguity becomes exploitable.
* Example: `You → CDN/LB (HTTPS) → HTTP/1.1 → origin webapp`

### Internal admin panels & dev/staging servers

* Many dashboards/APIs on `:80`, `:8080`, etc., no TLS, often behind shared pools.
* Targets like `http://intranet.corp/`, `http://dev-app.corp:8080`, `http://10.0.5.21/`.

### CDNs / load balancers that allow HTTP fallback

* Some allow both `http://` and `https://`. You can hit `http://` directly.

### IoT devices & embedded web servers

* Printers, cameras, routers, appliances commonly expose older HTTP/1.1 stacks.

---

## Installation

```bash
git clone https://github.com/<you>/http_smuggler.git
cd http_smuggler
```

---

## Directory Layout

```
http_smuggler/
├── http_smuggler.py          # main CLI
├── modules/
│   ├── scanner.py            # TE.CL / CL.TE probes (raw sockets)
│   ├── payload_generator.py  # TE.CL / CL.TE builders + custom
│   ├── payload_executor.py   # send verbatim payload + optional follow-up on same socket
│   ├── auto_detect.py        # [5] desync auto-detect + scoring
│   └── auto_exploit.py       # [6] cache poison / login hijack chaining
├── payloads/                 # generated or hand-written smuggle payloads
└── loot/                     # scan/detect/exec logs + reports
```

---

## Usage Overview

Launch with:

```bash
python3 http_smuggler.py
```

Menu:

<img width="1280" height="725" alt="Screenshot_2025-08-08_13_31_13" src="https://github.com/user-attachments/assets/4319b401-e9ec-48f5-b01b-415f5e644c06" />


> **Targets must be HTTP** (e.g., `http://host[:port]/`). The tool does not speak TLS.

---

## \[1] Scanner — Quick Recon

The scanner fires two desync probes:

* **TE.CL**: top request advertises `Transfer-Encoding: chunked` while also supplying `Content-Length`. Proxies typically honor TE; vulnerable origins may honor CL.
* **CL.TE**: top request supplies `Content-Length` and also advertises TE. Proxies may honor CL; vulnerable origins may honor TE.

Run:

```
[1] Scan a target for HTTP request smuggling
Target URL: http://host[:port]/
```

Output: `loot/<host>__scan.txt` with raw response snippets per vector. Scanner results are **heuristics**; move to executor to validate.

---

## \[2] Payload Generator — Build Reusable Smuggles

```
[2] Generate custom smuggle payloads
```

Options:

* **\[1] TE.CL Login Hijack Payload**

  * Top request for TE-first proxies; smuggled second request (e.g., `/login`).
  * Prompts: `Host`, `username`, `password`.
  * Saves: `payloads/tecl_login_<host>.txt`.

* **\[2] CL.TE Cache Poison Payload**

  * Top request for CL-first proxies; arbitrary body (redirect/JS/headers).
  * Saves: `payloads/clte_poison_<host>.txt`.

* **\[3] Custom Payload Builder**

  * Paste a fully hand-written request; saved verbatim.

Guidelines:

* Supply **host\[:port]** only when prompted for Host (no scheme).
* If you need a same-socket follow-up in \[4]/\[6]/\[7], put `Connection: keep-alive` in the top request.

---

## \[3] Loot Viewer

```
[3] View loot files
```

* Lists files in `loot/` and previews the head/tail of selected logs.
* Useful to quickly eyeball scan hits, detect scores, and exploit outcomes.

---

## \[4] Executor — Prove the Desync

```
[4] Execute a saved payload
```

Prompts:

* **Target**: `http://host[:port]/`
* **Payload path**: e.g., `payloads/tecl_login_<host>.txt`
* **Follow-up on same socket?** `y/n`

If `y`, paste a valid second raw HTTP request and end with a blank line plus `EOF`:

```
GET / HTTP/1.1
Host: host:port
Connection: close

EOF
```

Behavior:

* One TCP connection.
* Sends payload bytes exactly as written.
* Optional 0.5s sleep, then follow-up on the **same socket**.
* Logs full I/O: `loot/<host>_exec_<timestamp>.txt`.

What to look for:

* Frontend accepts top request; follow-up is rejected/consumed.
* Origin appears to treat smuggled bytes as a new top-of-stream request.

---

## \[5] Auto-Detect Desync (Scored)

This module turns the reconnaissance from \[1] into structured probes with **multiple variants** and assigns a **likelihood score** you can triage.

Run:

```
[5] Auto-detect desync (scored)
Target URL: http://host[:port]/
```

What it does:

* Fires controlled sets of TE.CL and CL.TE with small permutations:

  * Header order flips (`TE` before/after `CL`)
  * Header casing and spacing quirks
  * With/without `Connection: keep-alive`
  * Minimal vs padded chunk bodies
  * Duplicate `Content-Length` trials
* Observes frontend vs origin behaviors across timing and status codes.

Signals considered:

* **Split behavior** (e.g., `200` then anomalous `400`/timeout on follow-up).
* **Body length confusion** (origin responses truncated/queued).
* **Connection handling** (unexpected close mid-pipeline).
* **Timing skews** (follow-up delayed beyond threshold while socket stays open).

Scoring:

* Each signal contributes points; contradictory signals subtract.
* Final score in **0–100**:

  * `80–100` = High likelihood
  * `50–79`  = Medium likelihood
  * `<50`    = Low likelihood / needs manual tuning

Artifacts:

* Machine-readable JSON and human log:

  * `loot/<host>__detect.json`
  * `loot/<host>__detect.txt`
* Each probe includes exact bytes sent and deltas observed.

Next steps:

* Scores ≥ 80 → go straight to \[6] Auto-Exploit Chain.
* Scores 50–79 → try \[4] Executor with manual header tweaks.
* Scores < 50 → expand to custom payloads or different paths.

---

## \[6] Auto-Exploit Chain (Cache Poison / Login Hijack)

Given a confirmed or likely vector (from \[4] or \[5]), this module composes an end-to-end exploit against either a cache or a login flow.

Run:

```
[6] Auto-exploit chain (cache poison / login hijack)
Target URL: http://host[:port]/
Mode: [1] Cache poison  [2] Login hijack
```

Modes:

1. **Cache Poison**

* Crafts CL.TE or TE.CL according to the winning side from detection.
* Smuggles a cacheable response or poisoning marker:

  * Example body: `HTTP/1.1 200 OK` with short HTML/JS or `Location: /poison`
* Validates by hitting the poisoned path with a fresh GET.
* Artifacts:

  * Payload: `payloads/auto_cache_<host>.txt`
  * Evidence: `loot/<host>__cache_poison_<timestamp>.txt`

2. **Login Hijack**

* Crafts TE.CL or CL.TE top request carrying a smuggled `POST /login`.
* Prompts for creds or uses a default benign tuple if you choose.
* Watches for `Set-Cookie`/session markers in origin responses.
* Artifacts:

  * Payload: `payloads/auto_login_<host>.txt`
  * Evidence: `loot/<host>__login_hijack_<timestamp>.txt`

Safety rails:

* Optional **dry-run** to stop before follow-up confirmation.
* Throttling and maximum attempts to avoid noisy loops.
* All bytes and timings logged for reproducibility.

---

## \[7] Full Chain: Detect → Payload → Exploit

One key-press path from zero to evidence.

Run:

```
[7] Full chain: detect → payload → exploit
Target URL: http://host[:port]/
Chain: [1] Auto  [2] Guided
```

Flow:

* **Detect**: runs \[5], writes `__detect.json`, computes the winning vector.
* **Craft**:

  * Auto: chooses cache-poison if target looks cacheable, else login-hijack.
  * Guided: you pick poison vs hijack and can override headers and paths.
  * Saves payload under `payloads/auto_<mode>_<host>.txt`.
* **Exploit**: executes payload, performs same-socket follow-up, validates outcome.
* **Report**: generates a consolidated, timestamped report with:

  * Target, score, vector, payload path
  * Raw request/response excerpts
  * Cache-poison proof URL or captured cookies/markers
  * Next-step recommendations

Artifacts:

* `loot/<host>__fullchain_<timestamp>.txt`  (human)
* `loot/<host>__fullchain_<timestamp>.json` (machine-readable)

Use cases:

* Quick triage across many hosts
* Clean evidence packs for tickets/reports
* Repeatable runs after config changes

---

## Payload Notes (Framing and Hygiene)

* Always include a proper `Host` header; for nonstandard ports use `Host: host:port`.
* End header blocks with `\r\n\r\n`. Use `\r\n` everywhere.
* **TE.CL** top requests:

  * Include both `Transfer-Encoding: chunked` and `Content-Length: <n>`.
  * Use valid chunk framing, finishing with `0\r\n\r\n`, then smuggled bytes.
* **CL.TE**:

  * Intentionally mismatch `Content-Length` vs actual body to steer parsers.
* If you plan a same-socket follow-up, ensure `Connection: keep-alive` on the **top** request.

---

## Interpreting Results

* **200 via backend, 400/close on follow-up**: front normalized/closed; adjust keep-alive, CRLF, header ordering/casing.
* **Backend processes smuggled second request**: desync landed; move to \[6] or \[7].
* **Only 405/400s**: front likely normalizing ambiguity or path/method mismatch; try variants and custom payloads.

---

## Common Pitfalls

* Missing `Connection: keep-alive` on the top request when you want a two-stage probe.
* Forgetting the blank line at the end of the follow-up request (`\r\n\r\n`).
* Supplying full URLs where **host\[:port]** is expected, leading to bad filenames.
* Expecting HTTPS behavior. This tool is intentionally **HTTP-only**.

---

## Post-Smuggle Playbook

1. **Credential Injection (Login Hijack)**

* Inject a fake `POST /login` ahead of a victim’s request; capture `Set-Cookie`.

2. **Cache Poisoning → Persistent XSS / Redirects**

* Poison shared caches with HTML/JS or header manipulations.

3. **Pivot to Internal Panels**

* Change `Host:` to `intranet.corp` or `10.x.x.x`; target hidden admin routes.

4. **SSRF via Smuggling**

* Smuggle requests that trigger server-side fetches (metadata, internal APIs).

5. **Desync Chaining**

* Use one desync point to feed a second vulnerable hop deeper inside.

---

## Quickstart Summary

```bash
# 1) Clone
git clone https://github.com/<you>/http_smuggler.git
cd http_smuggler
mkdir -p payloads loot modules; touch modules/__init__.py

# 2) Run
python3 http_smuggler.py

# 3) Recon
[1] Scan → http://host[:port]/ → review loot/*__scan.txt

# 4) Build
[2] Generate → TE.CL Login or CL.TE Cache → payloads/*.txt
(Include Connection: keep-alive in top request if you plan a follow-up.)

# 5) Detect (scored)
[5] Auto-detect → loot/*__detect.{txt,json}

# 6) Exploit
[6] Auto-exploit → choose Cache or Login → loot/*__{cache_poison|login_hijack}_*.txt

# 7) Full Chain
[7] Full chain → single pass evidence + report → loot/*__fullchain_*.{txt,json}
```

---

## Disclaimer

Use only on systems and scopes where you have explicit, written authorization. You control every byte; act accordingly.

---

If you’re here, you already know: the only way to truly test HTTP/1.1 ambiguity is to **own the bytes on the wire**. This tool gives you that—without getting in your way.
![Screenshot_2025-08-07_12_53_58](https://github.com/user-attachments/assets/a1b0756d-b421-40a8-8b57-46b88e5da4db)

