#!/usr/bin/env python3
"""Scrape race cards for 2026-04-22"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper.scraper import HKJCResultsScraper as Scraper
from scraper.pipeline import HKJCDataPipeline as Pipeline

scraper = Scraper()
pipeline = Pipeline()

RACE_DATE = "2026-04-22"
RACECOURSE = "ST"  # Sha Tin

print(f"Scraping {RACE_DATE} at {RACECOURSE}...")

all_horses = []
for race_num in range(1, 12):  # Races 1-11
    try:
        print(f"  Race {race_num}...", end=" ")
        horses = scraper.scrape_race_card(RACE_DATE, race_num, RACECOURSE)
        if horses:
            print(f"{len(horses)} horses")
            all_horses.extend(horses)
        else:
            print("no data")
    except Exception as e:
        print(f"error: {e}")

print(f"\nTotal horses scraped: {len(all_horses)}")

if all_horses:
    print("Saving to database...")
    saved = pipeline.save_future_race_cards(all_horses)
    print(f"Saved: {saved} horses")
    
    # Show sample
    print("\nSample data:")
    for h in all_horses[:5]:
        print(f"  #{h['horse_number']}: {h['horse_name']} - {h['jockey']} ({h['trainer']})")