#!/usr/bin/env python3
"""
Targeted scraper for Feb 22 - Apr 12, 2026
Focuses on dates likely to have races (Wednesdays, weekends)
"""

import sys
import time
import logging
from datetime import datetime, timedelta

sys.path.insert(0, '.')

from scraper.pipeline import HKJCDataPipeline
from scraper.scraper import HKJCResultsScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def is_race_day(date):
    """Check if a date is a typical race day (Wed, Sat, Sun)"""
    weekday = date.weekday()
    return weekday in [2, 5, 6]  # Wed=2, Sat=5, Sun=6

def scrape_with_fallback(pipeline, date_str, course):
    """Try to scrape cards and results with course fallback"""
    total = 0
    
    for race_no in range(1, 13):
        try:
            count = pipeline.save_future_race_cards(date_str, course)
            if count > 0:
                total += count
                consecutive = 0
            else:
                consecutive += 1
                if consecutive >= 3:
                    break
        except:
            pass
        time.sleep(0.5)
    
    for race_no in range(1, 13):
        try:
            count = pipeline.save_race_results(date_str, course)
            if count > 0:
                total += count
                consecutive = 0
            else:
                consecutive += 1
                if consecutive >= 3:
                    break
        except:
            pass
        time.sleep(0.5)
    
    return total

def scrape_date(pipeline, date_str):
    """Scrape a date - try ST first, then HV if no data"""
    date = datetime.strptime(date_str, '%Y-%m-%d')
    weekday_name = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][date.weekday()]
    
    logger.info(f"\n📅 {date_str} ({weekday_name})")
    
    # Try Sha Tin first
    st_count = scrape_with_fallback(pipeline, date_str, 'ST')
    if st_count > 0:
        logger.info(f"  ✅ Sha Tin: {st_count} records")
        return st_count
    
    time.sleep(1)
    
    # Try Happy Valley
    hv_count = scrape_with_fallback(pipeline, date_str, 'HV')
    if hv_count > 0:
        logger.info(f"  ✅ Happy Valley: {hv_count} records")
        return hv_count
    
    logger.info(f"  ⚠️ No data")
    return 0

def main():
    logger.info("="*70)
    logger.info("🏇 SCRAPING FEB 22 - APR 12, 2026 (Targeted)")
    logger.info("="*70)
    logger.info("Focus on Wednesdays, Saturdays, Sundays")
    logger.info("="*70)
    
    pipeline = HKJCDataPipeline()
    
    # Generate dates
    start = datetime(2026, 2, 22)
    end = datetime(2026, 4, 12)
    
    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)
    
    # Filter to race days only (Wed, Sat, Sun)
    race_dates = [d for d in dates if is_race_day(datetime.strptime(d, '%Y-%m-%d'))]
    
    logger.info(f"Total dates: {len(dates)}")
    logger.info(f"Race days (Wed/Sat/Sun): {len(race_dates)}")
    logger.info("="*70)
    
    total_records = 0
    dates_with_data = []
    
    for i, date_str in enumerate(race_dates, 1):
        try:
            saved = scrape_date(pipeline, date_str)
            if saved > 0:
                total_records += saved
                dates_with_data.append(date_str)
                
            if i % 5 == 0:
                logger.info(f"\n📊 Progress: {i}/{len(race_dates)} dates checked, {total_records} records")
            
            time.sleep(3)  # Delay between dates
        except Exception as e:
            logger.error(f"  ❌ Error: {str(e)[:60]}")
            time.sleep(3)
    
    logger.info("\n" + "="*70)
    logger.info("📊 SUMMARY")
    logger.info("="*70)
    logger.info(f"Dates checked: {len(race_dates)}")
    logger.info(f"Dates with data: {len(dates_with_data)}")
    logger.info(f"Total records: {total_records}")
    if dates_with_data:
        logger.info(f"Dates: {', '.join(dates_with_data)}")
    logger.info("="*70)

if __name__ == '__main__':
    main()
