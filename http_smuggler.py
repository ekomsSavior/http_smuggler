#!/usr/bin/env python3
import os
from modules.scanner import run_scanner
from modules.payload_generator import generate_payload

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
    [0] Exit
""")

def main():
    banner()
    choice = input("Choose an option: ").strip()
    
    if choice == "1":
        target = input("Enter target URL (e.g., https://victim.com): ").strip()
        run_scanner(target)
    elif choice == "2":
        generate_payload()
    elif choice == "3":
        os.system("ls loot/")
    elif choice == "0":
        print("Goodbye 💀")
        exit()
    else:
        print("Invalid choice.")
    
if __name__ == "__main__":
    main()
