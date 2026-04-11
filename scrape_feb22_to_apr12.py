#!/usr/bin/env python3
"""
Scrape race data from February 22 to April 12, 2026
Non-aggressive scraping with delays between requests
"""

import sys
import time
import logging
from datetime import datetime, timedelta

sys.path.insert(0, '.')

from scraper.pipeline import HKJCDataPipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Dates to scrape: Feb 22 to Apr 12, 2026
def get_date_range():
    """Generate all dates from Feb 22 to Apr 12, 2026"""
    dates = []
    start = datetime(2026, 2, 22)
    end = datetime(2026, 4, 12)
    current = start
    while current <= end:
        dates.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)
    return dates

def scrape_date(pipeline, date_str):
    """Scrape a single date for both ST and HV courses"""
    logger.info(f"\n{'='*70}")
    logger.info(f"📅 Scraping {date_str}")
    logger.info(f"{'='*70}")
    
    total_saved = 0
    
    # Try Sha Tin first, then Happy Valley
    for course in ['ST', 'HV']:
        course_name = 'Sha Tin' if course == 'ST' else 'Happy Valley'
        logger.info(f"\n  🏟️ Trying {course_name} ({course})")
        
        course_saved = 0
        consecutive_empty = 0
        max_consecutive = 2  # Stop after 2 empty races
        
        # Scrape race cards
        for race_no in range(1, 13):
            try:
                count = pipeline.save_future_race_cards(date_str, course)
                if count > 0:
                    course_saved += count
                    consecutive_empty = 0
                    logger.info(f"    Race {race_no}: {count} cards saved")
                else:
                    consecutive_empty += 1
                    if consecutive_empty >= max_consecutive:
                        break
                time.sleep(0.8)  # Gentle delay
            except Exception as e:
                consecutive_empty += 1
                if consecutive_empty >= max_consecutive:
                    break
                time.sleep(1)
        
        # Delay between cards and results
        if course_saved > 0:
            time.sleep(1.5)
        
        # Scrape results
        consecutive_empty = 0
        for race_no in range(1, 13):
            try:
                count = pipeline.save_race_results(date_str, course)
                if count > 0:
                    course_saved += count
                    consecutive_empty = 0
                    logger.info(f"    Race {race_no}: {count} results saved")
                else:
                    consecutive_empty += 1
                    if consecutive_empty >= max_consecutive:
                        break
                time.sleep(0.8)  # Gentle delay
            except Exception as e:
                consecutive_empty += 1
                if consecutive_empty >= max_consecutive:
                    break
                time.sleep(1)
        
        if course_saved > 0:
            logger.info(f"  ✅ {course_name}: {course_saved} records")
            total_saved += course_saved
        else:
            logger.info(f"  ⚠️ No data at {course_name}")
        
        # Delay between courses
        time.sleep(2)
    
    return total_saved

def main():
    logger.info("="*70)
    logger.info("🏇 SCRAPING FEB 22 - APR 12, 2026")
    logger.info("="*70)
    logger.info("Non-aggressive scraping with delays")
    logger.info("Range: Feb 22 to Apr 12, 2026 (50 days)")
    logger.info("="*70)
    
    pipeline = HKJCDataPipeline()
    dates = get_date_range()
    
    logger.info(f"Total dates to check: {len(dates)}")
    
    total_records = 0
    dates_with_data = []
    dates_without_data = []
    
    for i, date_str in enumerate(dates, 1):
        try:
            saved = scrape_date(pipeline, date_str)
            
            if saved > 0:
                total_records += saved
                dates_with_data.append(f"{date_str} ({saved})")
                logger.info(f"✅ {date_str}: {saved} records saved")
            else:
                dates_without_data.append(date_str)
                logger.info(f"⚠️ {date_str}: No race data")
            
            # Progress update every 10 dates
            if i % 10 == 0:
                logger.info(f"\n📊 PROGRESS: {i}/{len(dates)} dates checked")
                logger.info(f"   Records so far: {total_records}")
                logger.info(f"   Dates with races: {len(dates_with_data)}")
            
            # Longer delay between dates (5 seconds)
            if i < len(dates):
                time.sleep(5)
            
        except Exception as e:
            logger.error(f"❌ {date_str}: Error - {str(e)[:100]}")
            dates_without_data.append(date_str)
            time.sleep(5)
    
    # Final summary
    logger.info("\n" + "="*70)
    logger.info("📊 FINAL SUMMARY")
    logger.info("="*70)
    logger.info(f"Total dates checked: {len(dates)}")
    logger.info(f"Dates with races: {len(dates_with_data)}")
    logger.info(f"Dates without races: {len(dates_without_data)}")
    logger.info(f"Total records saved: {total_records}")
    
    if dates_with_data:
        logger.info(f"\nDates with data:")
        for d in dates_with_data:
            logger.info(f"  ✅ {d}")
    
    if dates_without_data:
        logger.info(f"\nDates without data:")
        # Show in groups for brevity
        logger.info(f"  {len(dates_without_data)} dates had no race data")
    
    logger.info("="*70)

if __name__ == '__main__':
    main()
