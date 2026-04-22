#!/usr/bin/env python3
"""
Re-scrape race cards for dates with bad horse names.
Used to fix dates where scraper stored horse number instead of name.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper.scraper import Scraper
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Dates that need re-scraping (known bad dates or recent dates)
DATES_TO_RESCRAPE = [
    ("2026-04-12", "ST", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
    ("2026-04-13", "ST", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
    ("2026-04-19", "ST", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
    ("2026-04-20", "HV", [1, 2, 3, 4, 5, 6, 7, 8, 9]),
    ("2026-04-21", "ST", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
]

# Or auto-detect bad dates from database
def find_bad_dates():
    """Find dates where horse_name is just digits."""
    import sqlite3
    
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'hkjc_races.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Find dates with bad horse names in future_race_cards
    cursor.execute("""
        SELECT DISTINCT race_date, racecourse 
        FROM future_race_cards 
        WHERE horse_name GLOB '*[0-9]*' 
        AND LENGTH(horse_name) <= 4
        AND horse_name NOT LIKE '%[a-zA-Z]%'
    """)
    
    bad_dates = {}
    for row in cursor.fetchall():
        date, course = row[0], row[1]
        if date not in bad_dates:
            bad_dates[date] = []
        if course not in bad_dates[date]:
            bad_dates[date].append(course)
    
    conn.close()
    return bad_dates


def main():
    scraper = Scraper()
    
    print("=" * 50)
    print("Re-scraping race cards with bad horse names")
    print("=" * 50)
    
    # Option 1: Use explicit list
    # dates = DATES_TO_RESCRAPE
    
    # Option 2: Auto-detect bad dates
    bad_dates = find_bad_dates()
    if bad_dates:
        print(f"\nFound {len(bad_dates)} dates with bad data:")
        for date, courses in bad_dates.items():
            print(f"  {date}: {courses}")
        
        # Build list for re-scraping
        dates = []
        for date, courses in bad_dates.items():
            for course in courses:
                dates.append((date, course, list(range(1, 11))))  # races 1-10
    else:
        print("No bad dates found in database.")
        dates = DATES_TO_RESCRAPE
    
    total_saved = 0
    errors = 0
    
    for date, course, race_nums in dates:
        for race_num in race_nums:
            try:
                print(f"\nRe-scraping: {date} Race {race_num} ({course})...")
                
                # Scrape race card
                horses = scraper.scrape_race_card(date, race_num, course)
                
                if horses:
                    # Save to database
                    from scraper.pipeline import DataPipeline
                    pipeline = DataPipeline()
                    saved = pipeline.save_future_race_cards(horses)
                    total_saved += saved
                    print(f"  ✓ Saved {saved} horses")
                else:
                    print(f"  ✗ No horses found")
                    
            except Exception as e:
                errors += 1
                print(f"  ✗ Error: {e}")
                continue
    
    print("\n" + "=" * 50)
    print(f"Done! Total saved: {total_saved}, Errors: {errors}")
    print("=" * 50)


if __name__ == "__main__":
    main()