#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 1: 从实验服务器下载所有数据到本地 CSV
运行方式:
    python analysis/fetch_data.py --url https://picquiz.zeabur.app --secret study2-admin-2024
"""

import argparse
import os
import sys
import requests
import pandas as pd

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
        f.write(resp.content.decode('utf-8'))
    lines = resp.text.strip().count('\n')
    print(f"OK ({lines} rows) -> {filepath}")
    return True


def update_combined():
    """合并真实数据 + 合成数据 → *_combined.csv，fetch 后自动调用。"""
    pairs = [
        ('participants', 'participants_combined.csv'),
        ('responses',    'responses_combined.csv'),
        ('post-survey',  'post-survey_combined.csv'),
        ('interaction-logs', 'interaction-logs_combined.csv'),
    ]
    print("\nUpdating combined CSVs...")
    for base, combined_name in pairs:
        real_path  = os.path.join(OUTPUT_DIR, f'{base}.csv')
        synth_path = os.path.join(OUTPUT_DIR, f'{base}_synth.csv')
        out_path   = os.path.join(OUTPUT_DIR, combined_name)

        if not os.path.exists(real_path):
            print(f"  SKIP {combined_name} (real file missing)")
            continue
        if not os.path.exists(synth_path):
            print(f"  SKIP {combined_name} (synth file missing, run synthesize_data.py first)")
            continue

        real  = pd.read_csv(real_path)
        synth = pd.read_csv(synth_path)
        combined = pd.concat([real, synth], ignore_index=True)
        try:
            combined.to_csv(out_path, index=False, encoding='utf-8-sig')
            print(f"  OK {combined_name} ({len(real)} real + {len(synth)} synth = {len(combined)} rows)")
        except PermissionError:
            print(f"  WARN {combined_name} is open in another program, skipped")


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
    update_combined()


if __name__ == '__main__':
    main()
