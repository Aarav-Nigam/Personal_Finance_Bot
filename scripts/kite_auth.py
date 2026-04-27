#!/usr/bin/env python3
"""Standalone Kite Connect OAuth flow. Run daily to refresh the access token."""

from __future__ import annotations

import sys
import webbrowser
from urllib.parse import parse_qs, urlparse

from dotenv import set_key
from kiteconnect import KiteConnect

sys.path.insert(0, ".")
from config.settings import settings


def main():
    api_key = settings.KITE_API_KEY
    api_secret = settings.KITE_API_SECRET

    if not api_key or not api_secret:
        print("Error: KITE_API_KEY and KITE_API_SECRET must be set in .env")
        sys.exit(1)

    kite = KiteConnect(api_key=api_key)
    login_url = kite.login_url()

    print(f"\nOpening Kite login in browser...\n{login_url}\n")
    webbrowser.open(login_url)

    redirect_url = input("After logging in, paste the full redirect URL here: ").strip()

    parsed = urlparse(redirect_url)
    params = parse_qs(parsed.query)
    request_token = params.get("request_token", [None])[0]

    if not request_token:
        print("Error: Could not find request_token in the URL. Please try again.")
        sys.exit(1)

    try:
        session = kite.generate_session(request_token, api_secret=api_secret)
    except Exception as e:
        print(f"Error generating session: {e}")
        print("The request_token may have expired. Please re-run this script.")
        sys.exit(1)

    access_token = session["access_token"]
    set_key(".env", "KITE_ACCESS_TOKEN", access_token)

    masked = "..." + access_token[-6:]
    print(f"\nAccess token saved to .env ({masked})")
    print("Token expires at 6:00 AM IST tomorrow. Re-run this script daily.\n")


if __name__ == "__main__":
    main()
