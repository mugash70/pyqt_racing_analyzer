#!/usr/bin/env python3
"""
Fast scraper for Feb 22 - Apr 12, 2026 results only.
Skips quickly if no data found.
"""

import sys
import time
import logging
from datetime import datetime, timedelta

sys.path.insert(0, '.')

from scraper.pipeline import HKJCDataPipeline
import sqlite3

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_existing_results_dates(db_path='database/hkjc_races.db'):
    """Get dates that already have results"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT race_date FROM race_results 
        WHERE race_date BETWEEN '2026-02-22' AND '2026-04-12'
        ORDER BY race_date
    """)
    dates = {row[0] for row in cursor.fetchall()}
    conn.close()
    return dates

def scrape_results_fast(pipeline, date_str):
    """Scrape results only - skip fast if no data"""
    total = 0
    empty_count = 0
    max_empty = 2  # Stop after 2 empty races
    
    # Try Sha Tin
    for race_no in range(1, 13):
        try:
            count = pipeline.save_race_results(date_str, 'ST')
            if count > 0:
                total += count
                empty_count = 0
            else:
                empty_count += 1
                if empty_count >= max_empty:
                    break
            time.sleep(0.3)  # Small delay
        except Exception as e:
            empty_count += 1
            if empty_count >= max_empty:
                break
            time.sleep(0.3)
    
    if total > 0:
        return total, 'ST'
    
    # Try Happy Valley if no data at Sha Tin
    empty_count = 0
    for race_no in range(1, 13):
        try:
            count = pipeline.save_race_results(date_str, 'HV')
            if count > 0:
                total += count
                empty_count = 0
            else:
                empty_count += 1
                if empty_count >= max_empty:
                    break
            time.sleep(0.3)
        except Exception as e:
            empty_count += 1
            if empty_count >= max_empty:
                break
            time.sleep(0.3)
    
    return total, 'HV' if total > 0 else None

def main():
    logger.info("="*70)
    logger.info("🏇 FAST SCRAPER - RESULTS ONLY")
    logger.info("="*70)
    
    # Get dates that already have results
    existing_dates = get_existing_results_dates()
    logger.info(f"Dates already with results: {len(existing_dates)}")
    
    # Generate all dates from Feb 22 to Apr 12
    start = datetime(2026, 2, 22)
    end = datetime(2026, 4, 12)
    all_dates = []
    current = start
    while current <= end:
        date_str = current.strftime('%Y-%m-%d')
        if date_str not in existing_dates:
            all_dates.append(date_str)
        current += timedelta(days=1)
    
    logger.info(f"Dates to check: {len(all_dates)}")
    logger.info("="*70)
    
    if not all_dates:
        logger.info("All dates already have results! Nothing to scrape.")
        return
    
    pipeline = HKJCDataPipeline()
    
    total_saved = 0
    dates_with_data = []
    dates_without_data = []
    
    for i, date_str in enumerate(all_dates, 1):
        weekday = datetime.strptime(date_str, '%Y-%m-%d').strftime('%a')
        logger.info(f"\n[{i}/{len(all_dates)}] {date_str} ({weekday})")
        
        try:
            count, course = scrape_results_fast(pipeline, date_str)
            
            if count > 0:
                total_saved += count
                dates_with_data.append(date_str)
                logger.info(f"  ✅ {course}: {count} results")
            else:
                dates_without_data.append(date_str)
                logger.info(f"  ⚠️ No data")
            
            # Small delay between dates
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"  ❌ Error: {str(e)[:60]}")
            dates_without_data.append(date_str)
            time.sleep(1)
    
    # Summary
    logger.info("\n" + "="*70)
    logger.info("📊 FINAL SUMMARY")
    logger.info("="*70)
    logger.info(f"Dates checked: {len(all_dates)}")
    logger.info(f"Dates with results: {len(dates_with_data)}")
    logger.info(f"Dates without results: {len(dates_without_data)}")
    logger.info(f"Total results saved: {total_saved}")
    
    if dates_with_data:
        logger.info(f"\nDates with data: {', '.join(dates_with_data)}")
    
    logger.info("="*70)

if __name__ == '__main__':
    main()
