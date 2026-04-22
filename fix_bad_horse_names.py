#!/usr/bin/env python3
"""
Re-scrape race cards for dates with bad horse names.
Uses the scraper to fetch fresh correct data from HKJC.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper.scraper import HKJCResultsScraper as Scraper
from scraper.pipeline import HKJCDataPipeline as DataPipeline
import sqlite3

db_path = os.path.join(os.path.dirname(__file__), 'database', 'hkjc_races.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("Finding bad horse names in future_race_cards...")

# Find rows where horse_name is just digits
cursor.execute("""
    SELECT DISTINCT race_date, race_number, racecourse
    FROM future_race_cards 
    WHERE (horse_name GLOB '*[0-9]*' AND LENGTH(horse_name) <= 4 AND horse_name NOT LIKE '%[a-zA-Z]%')
    OR horse_name IS NULL 
    OR horse_name = ''
    ORDER BY race_date, race_number
""")

bad_dates = cursor.fetchall()
print(f"Found {len(bad_dates)} races with bad horse names")

if not bad_dates:
    print("No bad data found!")
    conn.close()
    exit()

# Show summary
print("\nAffected races:")
for row in bad_dates[:10]:
    print(f"  {row['race_date']} R{row['race_number']} ({row['racecourse']})")
if len(bad_dates) > 10:
    print(f"  ... and {len(bad_dates) - 10} more")

print("\nRe-scraping...")

scraper = Scraper()
pipeline = DataPipeline()
fixed = 0
errors = 0

for row in bad_dates:
    race_date = row['race_date']
    race_num = row['race_number']
    racecourse = row['racecourse']
    
    try:
        # Normalize racecourse (remove extra info)
        if 'ST' in racecourse.upper():
            course = 'ST'
        elif 'HV' in racecourse.upper():
            course = 'HV'
        else:
            course = racecourse[:2].strip()
        
        print(f"  Scraping {race_date} R{race_num} ({course})...")
        horses = scraper.scrape_race_card(race_date, race_num, course)
        
        if horses:
            # Delete old bad data
            cursor.execute("""
                DELETE FROM future_race_cards 
                WHERE race_date LIKE ? AND race_number = ? AND racecourse LIKE ?
            """, (f"{race_date.split(' ')[0]}%", race_num, f"{course}%"))
            
            # Save new data
            saved = pipeline.save_future_race_cards(horses)
            fixed += saved
            print(f"    ✓ Saved {saved} horses")
        else:
            print(f"    ✗ No horses returned")
            errors += 1
            
    except Exception as e:
        print(f"    ✗ Error: {e}")
        errors += 1
        continue

conn.commit()
conn.close()

print(f"\nDone! Saved {fixed} horses, {errors} errors.")
