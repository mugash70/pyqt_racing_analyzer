#!/usr/bin/env python3
"""Check all table types on rankings pages"""

import requests
from bs4 import BeautifulSoup

def check_all_tables(name, url):
    response = requests.get(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    soup = BeautifulSoup(response.text, 'html.parser')
    
    print(f"\n=== {name} ===")
    
    # Check ALL tables (not just table_bd)
    all_tables = soup.find_all('table')
    print(f"Total tables found: {len(all_tables)}")
    
    for i, table in enumerate(all_tables):
        print(f"\nTable {i+1} (class: {table.get('class', 'no-class')}):")
        rows = table.find_all('tr')
        print(f"  Rows: {len(rows)}")
        
        for j, row in enumerate(rows[:10]):  # First 10 rows
            cols = row.find_all(['td', 'th'])
            if cols and len(cols) > 1:
                col_texts = [col.text.strip()[:15] for col in cols[:8]]
                print(f"  Row {j}: {col_texts}")
                
                # Look for actual data (names with numbers)
                if len(cols) >= 3:
                    first_col = cols[0].text.strip()
                    second_col = cols[1].text.strip()
                    if (first_col and 
                        first_col not in ['騎師榜', '騎師', '練馬師榜', '練馬師', '上季資料', '(不包括海外賽績及獎金)'] and
                        (second_col.isdigit() or any(col.text.strip().isdigit() for col in cols[1:4]))):
                        print(f"    *** POTENTIAL DATA: {[col.text.strip() for col in cols]}")
    
    # Check for dynamic content indicators
    scripts = soup.find_all('script')
    has_nextjs = any('__NEXT_DATA__' in script.text for script in scripts if script.string)
    has_react = any('React' in script.text for script in scripts if script.string)
    
    print(f"\nDynamic content indicators:")
    print(f"  NextJS: {has_nextjs}")
    print(f"  React: {has_react}")

# Check both ranking pages
urls = [
    ("Jockey Rankings", "https://racing.hkjc.com/zh-hk/local/info/jockey-ranking"),
    ("Trainer Rankings", "https://racing.hkjc.com/zh-hk/local/info/trainer-ranking"),
]

for name, url in urls:
    check_all_tables(name, url)