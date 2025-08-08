#!/usr/bin/env python3
import os
import sys
from modules.scanner import run_scanner
from modules.payload_generator import generate_payload
from modules.payload_executor import execute_payload

def banner():
    print(r"""
░██     ░██    ░██       ░██                             ░██████                                                    ░██                     
░██     ░██    ░██       ░██                            ░██   ░██                                                   ░██                     
░██     ░██ ░████████ ░████████ ░████████              ░██         ░█████████████  ░██    ░██  ░████████  ░████████ ░██  ░███████  ░██░████ 
░██████████    ░██       ░██    ░██    ░██              ░████████  ░██   ░██   ░██ ░██    ░██ ░██    ░██ ░██    ░██ ░██ ░██    ░██ ░███     
░██     ░██    ░██       ░██    ░██    ░██                     ░██ ░██   ░██   ░██ ░██    ░██ ░██    ░██ ░██    ░██ ░██ ░█████████ ░██      
░██     ░██    ░██       ░██    ░███   ░██              ░██   ░██  ░██   ░██   ░██ ░██   ░███ ░██   ░███ ░██   ░███ ░██ ░██        ░██      
░██     ░██     ░████     ░████ ░██░█████  ░██████████   ░██████   ░██   ░██   ░██  ░█████░██  ░█████░██  ░█████░██ ░██  ░███████  ░██      
                                ░██                                                                  ░██        ░██                         
                                ░██                                                            ░███████   ░███████                          

HTTP Smuggler - Desync Recon Scanner
By ekomsSavior

    [1] Scan a target for HTTP request smuggling
    [2] Generate custom smuggle payloads
    [3] View loot files
    [4] Execute a saved payload
    [0] Exit
""")

def ensure_dirs():
    os.makedirs("loot", exist_ok=True)
    os.makedirs("payloads", exist_ok=True)

def list_loot():
    ensure_dirs()
    entries = sorted(
        (f for f in os.listdir("loot")),
        key=lambda x: os.path.getmtime(os.path.join("loot", x)),
        reverse=True
    )
    if not entries:
        print("[-] No loot yet. Run a scan or execute a payload first.\n")
        return
    print("\n=== loot/ ===")
    for f in entries:
        path = os.path.join("loot", f)
        size = os.path.getsize(path)
        print(f"{f}  ({size} bytes)")
    print("")

def main():
    ensure_dirs()
    while True:
        banner()
        choice = input("Choose an option: ").strip()

        if choice == "1":
            target = input("Enter target URL (HTTP only, e.g., http://victim.com): ").strip()
            if not target.startswith("http://"):
                print("[!] HTTP only. Use a URL like: http://host[:port]/\n")
                continue
            run_scanner(target)

        elif choice == "2":
            generate_payload()

        elif choice == "3":
            list_loot()

        elif choice == "4":
            target = input("Enter target URL (HTTP only, e.g., http://victim.com): ").strip()
            if not target.startswith("http://"):
                print("[!] HTTP only. Use a URL like: http://host[:port]/\n")
                continue
            payload_path = input("Path to payload file (e.g., payloads/tecl_login_victim_com.txt): ").strip()

            use_follow_up = input("Send a follow-up request on the SAME socket? (y/n): ").strip().lower() == "y"
            follow_up_req = None
            delay = 0.5
            if use_follow_up:
                print("\nPaste the FULL follow-up request (raw HTTP). End with a single line 'EOF'.")
                lines = []
                while True:
                    line = input()
                    if line.strip() == "EOF":
                        break
                    lines.append(line)
                follow_up_req = "\r\n".join(lines)
                try:
                    delay = float(input("Delay before follow-up (seconds, default 0.5): ").strip() or "0.5")
                except:
                    delay = 0.5

            execute_payload(
                target,
                payload_path,
                send_follow_up=use_follow_up,
                follow_up_req=follow_up_req,
                follow_up_delay=delay
            )

        elif choice == "0":
            print("Goodbye 💀")
            sys.exit(0)

        else:
            print("Invalid choice.\n")

if __name__ == "__main__":
    main()
