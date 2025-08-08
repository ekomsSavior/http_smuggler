# HTTP Smuggler — Desync Recon & Exploitation 
HTTP Smuggler is a focused HTTP/1.1 request-smuggling reconnaissance and exploitation tool for advanced operators. It sends **raw**, hand-crafted HTTP/1.1 requests over plain TCP using sockets—no HTTP client libraries, no HTTPS, no Burp. It’s designed for environments where **frontend reverse proxies** multiplex user traffic to **origin servers** over **upstream HTTP/1.1** and ambiguities in request framing can be abused to create a **desynchronization (desync)** between the two.

The tool bundles three workflows:

* **Scanner** — quick TE.CL / CL.TE desync probes.
* **Payload Generator** — build reusable smuggle payloads (TE.CL login injection, CL.TE cache poison, or fully custom).
* **Executor** — send saved payloads verbatim, optionally followed by a second request on the **same socket** to confirm desync effects.

> Scope: **HTTP only**. No TLS. The point is unmediated control over framing (`Content-Length`, `Transfer-Encoding`, body). Use your own TCP egress controls and OPSEC.

![Screenshot_2025-08-07_12_53_58](https://github.com/user-attachments/assets/60ed48e4-5f7c-4272-86d4-56ba4b9100de)

---

## Why HTTP Smuggling Still Matters

The **real danger zone** for HTTP request smuggling is not the browser→edge TLS link. It’s **inside infrastructure** where **HTTP/1.1** is still common:

### Reverse proxy → origin server links

* Client may use HTTPS, but the edge often talks to the origin over **raw HTTP/1.1** within the data center.
* That upstream hop is where parsing ambiguity becomes exploitable.
* Example:

  ```
  You → CDN/LB (HTTPS) → HTTP/1.1 → origin webapp
  ```

  If your request reaches the proxy in a form that exercises HTTP/1.1 ambiguity, you can desync proxy vs. origin parsing.

### Internal admin panels & dev/staging servers

* Many internal dashboards, APIs, CI/stage boxes don’t bother with TLS.
* Typical targets:

  * `http://intranet.corp/`
  * `http://dev-app.corp:8080`
  * `http://10.0.5.21/`
* These are prime smuggle candidates, especially behind shared upstream pools.

### CDNs / load balancers that allow HTTP fallback

* Some configurations allow both `http://` and `https://`.
* You can use `http://` directly and avoid TLS entirely.

### IoT devices & embedded web servers

* Printers, cameras, routers, IoT hubs commonly expose old HTTP/1.1 stacks.
* Example: `http://192.168.0.50/`

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
├── http_smuggler.py        # main CLI
├── modules/
│   ├── scanner.py          # TE.CL / CL.TE probes (raw sockets)
│   ├── payload_generator.py # TE.CL / CL.TE builders + custom
│   └── payload_executor.py  # send verbatim payload + follow-up on same socket
├── payloads/               # generated or hand-written smuggle payloads
└── loot/                   # scan+execution logs
```

---

## Usage Overview

Launch with:

```bash
python3 http_smuggler.py
```

Menu:

```
[1] Scan a target for HTTP request smuggling
[2] Generate custom smuggle payloads
[3] View loot files
[4] Execute a saved payload
[0] Exit
```

> **Targets must be HTTP** (e.g., `http://host[:port]/`). The tool does not speak TLS.

---

## 1) Scanner — Quick Recon

The scanner sends two desync probes:

* **TE.CL**: top request advertises `Transfer-Encoding: chunked` while also supplying `Content-Length`. Proxies typically honor TE; vulnerable origins may honor CL.
* **CL.TE**: top request supplies `Content-Length` and also advertises TE. Proxies may honor CL; vulnerable origins may honor TE.

Run:

```
[1] Scan a target for HTTP request smuggling
Target URL: http://host[:port]/
```

Output is saved to `loot/<host>__scan.txt` with raw response snippets per vector. Treat scanner results as **heuristics**; different devices normalize or reject ambiguity differently. Move to executor to validate.

---

## 2) Payload Generator — Build Reusable Smuggles

```
[2] Generate custom smuggle payloads
```

Options:

* **\[1] TE.CL Login Hijack Payload**
  Builds a top request shaped for TE-first proxies with a smuggled second request (e.g., `/login` with credentials). You’ll provide `Host`, `username`, `password`. The generator writes to `payloads/tecl_login_<host>.txt`.
* **\[2] CL.TE Cache Poison Payload**
  Builds a top request shaped for CL-first proxies with an arbitrary “poison” body you supply (e.g., redirect or JS).
* **\[3] Custom Payload Builder**
  Paste a fully hand-written request; tool will save exactly what you typed, verbatim.

**Important:** When prompted for “Target host”, supply **host\[:port] only** (no `http://`), e.g. `127.0.0.1:8080`. If you paste a full URL, normalize filenames manually or update the generator to sanitize input.

**Keep-alive advisory:** Many desync techniques require the connection to persist for the follow-up. Include `Connection: keep-alive` in the **top request** headers when you intend to send a follow-up probe on the same socket.

---

## 3) Executor — Prove the Desync

```
[4] Execute a saved payload
```

Prompts:

* **Target**: `http://host[:port]/` (HTTP only)
* **Payload path**: e.g. `payloads/tecl_login_<host>.txt`
* **Follow-up on same socket?**
  If `y`, paste a second raw HTTP request. End input with a **blank line** followed by `EOF`.

Example follow-up probe:

```
GET / HTTP/1.1
Host: host:port
Connection: close

EOF
```

The executor:

* Opens one TCP connection.
* Sends your payload **exactly as written**.
* Optionally sleeps \~0.5s and sends the follow-up on the **same socket**.
* Captures the full response and writes a complete log to `loot/<host>_exec_<timestamp>.txt`, including the exact bytes sent.

**What to look for**

* Frontend accepts the top request (200 to origin).
* The follow-up is rejected at the frontend **or** appears to be “eaten” or delayed.
* The origin shows unexpected `Body-len-seen` behavior or clearly treats the smuggled second request as a new top-of-stream request.

---

## Payload Notes (Framing and Hygiene)

* Always include a proper `Host` header. If the service listens on a nonstandard port, use `Host: host:port`.
* Ensure request lines and headers are terminated with `\r\n`, and the header block is followed by an empty line (`\r\n\r\n`).
* For **TE.CL** top requests, include:

  ```
  Transfer-Encoding: chunked
  Content-Length: <some number>
  ```

  And ensure chunked framing is syntactically valid (e.g., `0\r\n\r\n` to end the chunked body) before introducing the smuggled second request bytes.
* For **CL.TE**, mismatching `Content-Length` vs. bytes actually sent is the point, but ensure you still produce a syntactically parseable sequence for the device that “wins.”

---

## Interpreting Results

* **200 via backend, 400 `<BADREQ>` on follow-up at frontend**: front device normalized/rejected the follow-up or closed the connection; adjust keep-alive and CRLF discipline, or fuzz header ordering/casing.
* **Backend appears to process the smuggled second request**: desync landed. Validate impact paths (cache poisoning, session fixation/hijack, credential stuffing) responsibly, in scope.
* **Only 405/400s**: front is likely normalizing out the ambiguity (or the target path requires a method other than POST). Move to custom payloads and variants (duplicated headers, case/space quirks, chunk-ext, etc.).

---

## Common Pitfalls

* Missing `Connection: keep-alive` on the **top** request while attempting a two-stage probe on the same socket.
* Omitting the **blank line** at the end of the follow-up request (HTTP/1.1 requires `\r\n\r\n` to terminate headers).
* Supplying a full URL as “host” in the generator, causing unsafe filenames. Use `host[:port]` only (e.g., `127.0.0.1:8080`).
* Expecting HTTPS behavior. This tool does **not** speak TLS by design.

---

## When to Use HTTP Smuggler

* You suspect **reverse proxy → origin** upstream is **HTTP/1.1** with connection reuse.
* You are assessing **internal HTTP** services (admin, IoT, dev/stage).
* You need **full control** of framing and cannot risk client libraries silently normalizing your requests.
* You want a repeatable, scriptable path to go from recon → payload craft → verification logs.

---

### **Post-Smuggle Playbook**

Once you confirm an HTTP smuggling vector, here’s where to take it:

#### **1. Credential Injection (Login Hijack)**

* Build a TE.CL or CL.TE payload that **injects a fake login POST** ahead of a legitimate user’s request.
* Watch server logs / captured responses for `Set-Cookie` headers with valid session IDs.
* Replay those cookies against the origin service.

#### **2. Cache Poisoning → Persistent XSS / Redirects**

* Smuggle a response containing malicious headers or HTML into a shared cache (e.g., Varnish, CDN edge node).
* Next user to hit that path will get your poisoned content.
* Great for turning a desync into full user compromise or phishing.

#### **3. Pivot to Internal Panels**

* If the smuggle happens inside a proxy that can reach internal hosts:

  * Change `Host:` to point at `intranet.corp` or `10.x.x.x`.
  * Craft requests targeting hidden admin routes.
* If auth cookies are shared, you might walk straight into authenticated dashboards.

#### **4. SSRF via Smuggling**

* Some backends will fetch URLs from request bodies or headers.
* Smuggle a request that triggers SSRF inside the origin server.
* Can chain into cloud metadata access (`169.254.169.254`) or internal API calls.

#### **5. Desync Chaining**

* Use one desync point to feed payloads into another vulnerable system behind it.
* Example:

  * CloudFront → load balancer → origin API.
  * Smuggle into LB, then smuggle again into API for double-layer bypass.

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

# 5) Prove
[4] Execute → choose payload → paste follow-up GET / on same socket
→ analyze loot/*_exec_*.txt

# 6) Post-Smuggle Playbook
>>> follow the white rabbit..
```
## Disclaimer

Use only on systems and scopes where you have explicit, written authorization..

---
If you’re here, you already know: the only way to truly test HTTP/1.1 ambiguity is to **own the bytes on the wire**. This tool gives you that, without getting in your way.

![Screenshot_2025-08-07_12_53_58](https://github.com/user-attachments/assets/11d770f2-ddcc-419f-aa33-1cf9dc6f89a2)

