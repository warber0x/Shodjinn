# ###################################################################################

# Shodan Account Automation Script
# ===============================

# Author: Thered0ne
# Date: 2025-10-01
# Version: 1.0

# Description:
# ------------
# Automates Shodan account registration using Guerrilla Mail, activates the account,
# logs in, and retrieves the API key. Supports normal mode (verbose) and pipe mode
# (for automation).

# Dependencies:
# -------------
# - requests
# - beautifulsoup4

# Usage:
# ------
# python shodjinn.py          # Normal mode
# python shodjinn.py | other  # Pipe mode for automation
# ###################################################################################

import re
import requests
import time
import itertools
import sys
import threading
from bs4 import BeautifulSoup

GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

API = "https://api.guerrillamail.com/ajax.php"
SHODAN_REG_URL = "https://account.shodan.io/register"
SHODAN_POST_URL = "https://account.shodan.io/register"
SHODAN_LOGIN_PAGE = "https://account.shodan.io/login"
SHODAN_ACCOUNT_URL = "https://account.shodan.io/"

PIPE_MODE = not sys.stdout.isatty()

def banner():
    if not PIPE_MODE:
        print(r"""
       .     ✦
      / \~~~/ \
     (  °   °  )
      \  ~~~  /
     / '-----' \
    | SHODJINN |
    |   v1.0   |
    """)

def call_api(params, session):
    params["ip"] = "127.0.0.1"
    params["agent"] = "Mozilla/5.0 (compatible)"
    return session.get(API, params=params)

def create_mailbox(session):
    resp = call_api({"f": "get_email_address"}, session)
    resp.raise_for_status()
    return resp.json()["email_addr"]

def check_mail(session, seq=0):
    resp = call_api({"f": "check_email", "seq": seq}, session)
    resp.raise_for_status()
    return resp.json()

def fetch_mail(session, mail_id):
    resp = call_api({"f": "fetch_email", "email_id": mail_id}, session)
    resp.raise_for_status()
    return resp.json()

def register(session, email):
    r = session.get(SHODAN_REG_URL, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    token_input = soup.find("input", {"name": "csrf_token"})
    if not token_input or not token_input.get("value"):
        if not PIPE_MODE:
            print(f"{YELLOW}[!]{RESET} CSRF token not found on registration page.")
        raise SystemExit(1)
    csrf_token = token_input["value"]

    payload = {
        "username": email,
        "password": "#Password123#",
        "password_confirm": "#Password123#",
        "email": email,
        "csrf_token": csrf_token,
    }
    headers = {"Referer": SHODAN_REG_URL}
    resp = session.post(SHODAN_POST_URL, data=payload, headers=headers, timeout=15, allow_redirects=True)
    return resp.status_code

def extract_activation_link(html):
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if "/activate/" in href:
            return href
    m = re.search(r"https?://\S*/activate/[A-Za-z0-9]+", soup.get_text(" ", strip=True))
    if m:
        return m.group(0)
    return None

def activate_link_get(url, session, timeout=15):
    resp = session.get(url, timeout=timeout, allow_redirects=True)
    return resp

def fetch_csrf_from_page(session, url):
    r = session.get(url, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    token_input = soup.find("input", {"name": "csrf_token"})
    if token_input and token_input.get("value"):
        return token_input["value"]
    return None

def login(session, username, password):
    csrf = None
    try:
        csrf = fetch_csrf_from_page(session, SHODAN_LOGIN_PAGE)
    except requests.RequestException:
        csrf = None

    form = {
        "username": "+" + username,
        "password": password,
        "grant_type": "password",
        "continue": SHODAN_LOGIN_PAGE,
    }
    if csrf:
        form["csrf_token"] = csrf

    headers = {"Referer": SHODAN_LOGIN_PAGE}
    resp = session.post(SHODAN_LOGIN_PAGE, data=form, headers=headers, timeout=15, allow_redirects=True)
    return resp

def get_api_key(session):
    try:
        r = session.get(SHODAN_ACCOUNT_URL, timeout=15)
        r.raise_for_status()
    except requests.RequestException:
        return None
    soup = BeautifulSoup(r.text, "html.parser")
    key_input = soup.find("input", {"id": "api_key"})
    if key_input and key_input.get("value"):
        return key_input["value"]
    m = re.search(r"[0-9A-Fa-f]{32}", r.text)
    if m:
        return m.group(0)
    return None

def spinner_task(stop_event, message="Waiting for email..."):
    spinner = itertools.cycle("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏")
    while not stop_event.is_set():
        if not PIPE_MODE:  # spinner only in normal mode
            sys.stdout.write(f"\r[{next(spinner)}] {message}")
            sys.stdout.flush()
        time.sleep(0.08)
    if not PIPE_MODE:
        sys.stdout.write("\r" + " " * (len(message) + 10) + "\r")
        sys.stdout.flush()

def main():
    banner()

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
    })

    email_addr = create_mailbox(session)
    if not PIPE_MODE:
        print("[*] Using the email address:", email_addr)

    status = register(session, email_addr)
    if status != 200:
        if not PIPE_MODE:
            print(f"{YELLOW}[!]{RESET} Cannot register! server returned {status}")
        raise SystemExit(1)

    if not PIPE_MODE:
        print(f"[{GREEN}\u2713{RESET}] Registration done!")

    stop_spinner = threading.Event()
    spinner_thread = threading.Thread(target=spinner_task, args=(stop_spinner,))
    spinner_thread.start()

    seq = 1
    finish_after = False
    try:
        while True:
            data = check_mail(session, seq)
            mail_list = data.get("list", [])
            if mail_list:
                stop_spinner.set()
                spinner_thread.join()
                if not PIPE_MODE:
                    print(f"[{GREEN}\u2713{RESET}] Email received!")

                for mail in mail_list:
                    mail_id = mail.get("mail_id")
                    full = fetch_mail(session, mail_id)

                    if full.get("mail_from") == "no-reply@mg.shodan.io":
                        finish_after = True
                        link = extract_activation_link(full.get("mail_body", ""))
                        if not link:
                            if not PIPE_MODE:
                                print(f"{YELLOW}!{RESET} Activation link not found.")
                            raise SystemExit(1)
                        resp = activate_link_get(link, session=session)
                        if 200 <= resp.status_code < 300:
                            if not PIPE_MODE:
                                print(f"[{GREEN}\u2713{RESET}] Activation succeeded.")
                        else:
                            if not PIPE_MODE:
                                print(f"{YELLOW}!{RESET} Activation failed.")
                            raise SystemExit(1)

                        login_resp = login(session, username=email_addr, password="#Password@123#")
                        if 200 <= login_resp.status_code < 300:
                            api_key = get_api_key(session)
                            if api_key:
                                if PIPE_MODE:
                                    print(api_key)  # ONLY the key in pipe mode
                                else:
                                    print(f"[{GREEN}\u2713{RESET}] Your Shodan API key: {api_key}")
                            else:
                                if not PIPE_MODE:
                                    print(f"{YELLOW}[!]{RESET} Could not find API key.")
                        else:
                            if not PIPE_MODE:
                                print(f"{YELLOW}[!]{RESET} Login failed!")

                if finish_after:
                    break
            time.sleep(5)
    except KeyboardInterrupt:
        stop_spinner.set()
        spinner_thread.join()
        if not PIPE_MODE:
            print("\nInterrupted by user.")

if __name__ == "__main__":
    main()
