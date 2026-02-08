#!/usr/bin/env python3
"""Detailed check of failing URLs to see actual data"""

import requests
from bs4 import BeautifulSoup

def check_detailed(name, url):
    try:
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print(f"\n=== {name} ===")
        
        # Check all tables
        tables = soup.find_all('table')
        for i, table in enumerate(tables):
            print(f"\nTable {i+1}:")
            rows = table.find_all('tr')
            for j, row in enumerate(rows[:5]):  # First 5 rows
                cols = row.find_all(['td', 'th'])
                if cols:
                    col_data = []
                    for col in cols[:8]:  # First 8 columns
                        text = col.text.strip()[:15]  # First 15 chars
                        col_data.append(text)
                    print(f"  Row {j}: {col_data}")
                    
                    # If this looks like data (has numbers), show more
                    if any(col.text.strip().isdigit() for col in cols[:3]):
                        print(f"    FULL ROW: {[col.text.strip() for col in cols]}")
                        
        # Check for NextJS data
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and ('window.__NEXT_DATA__' in script.string or 'props' in script.string):
                print(f"\nNextJS data found in script")
                break
                
    except Exception as e:
        print(f"\n{name}: ERROR - {str(e)}")

# Check the ranking pages specifically
urls = [
    ("Jockey Rankings", "https://racing.hkjc.com/zh-hk/local/info/jockey-ranking"),
    ("Trainer Rankings", "https://racing.hkjc.com/zh-hk/local/info/trainer-ranking"),
]

for name, url in urls:
    check_detailed(name, url)