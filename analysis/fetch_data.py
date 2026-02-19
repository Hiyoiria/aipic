#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 1: 从实验服务器下载所有数据到本地 CSV
运行方式:
    python analysis/fetch_data.py --url https://your-app.zeabur.app --secret your-admin-secret
"""

import argparse
import os
import sys
import requests

sys.stdout.reconfigure(encoding='utf-8')

COLLECTIONS = ['participants', 'responses', 'post-survey', 'interaction-logs']
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'data')


def fetch_collection(base_url, secret, collection):
    url = f"{base_url.rstrip('/')}/api/admin/export?collection={collection}"
    headers = {'x-admin-secret': secret}
    print(f"  Fetching {collection}...", end=' ')
    resp = requests.get(url, headers=headers, timeout=60)
    if resp.status_code != 200:
        print(f"FAILED (HTTP {resp.status_code})")
        print(f"    Response: {resp.text[:200]}")
        return False
    filepath = os.path.join(OUTPUT_DIR, f"{collection}.csv")
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        f.write(resp.text)
    lines = resp.text.strip().count('\n')
    print(f"OK ({lines} rows) -> {filepath}")
    return True


def main():
    parser = argparse.ArgumentParser(description='Download experiment data')
    parser.add_argument('--url', required=True, help='Base URL of the experiment app')
    parser.add_argument('--secret', required=True, help='Admin secret')
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Downloading data from {args.url}\n")

    success = 0
    for c in COLLECTIONS:
        if fetch_collection(args.url, args.secret, c):
            success += 1

    print(f"\nDone: {success}/{len(COLLECTIONS)} collections downloaded to {OUTPUT_DIR}/")


if __name__ == '__main__':
    main()
