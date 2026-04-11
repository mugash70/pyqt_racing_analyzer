#!/usr/bin/env python3
"""
Gentle scraper for February 12-22, 2026 data.
Non-aggressive scraping with delays between requests.
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

# Dates to scrape with their likely tracks
# HKJC typically races on Wednesdays (Happy Valley) and weekends (Sha Tin)
DATES_TO_SCRAPE = [
    # (date_str, course, description)
    ('2026-02-12', 'ST', 'Thursday - likely Sha Tin'),
    ('2026-02-13', 'ST', 'Friday - likely Sha Tin'),
    ('2026-02-14', 'ST', 'Saturday - Sha Tin (CNY meeting)'),
    ('2026-02-15', 'HV', 'Sunday - Happy Valley (CNY meeting)'),
    ('2026-02-16', 'ST', 'Monday - likely Sha Tin'),
    ('2026-02-17', 'ST', 'Tuesday - likely Sha Tin'),
    ('2026-02-18', 'HV', 'Wednesday - Happy Valley'),
    ('2026-02-19', 'ST', 'Thursday - Sha Tin (has cards, needs results)'),
    ('2026-02-20', 'ST', 'Friday - likely Sha Tin'),
    ('2026-02-21', 'ST', 'Saturday - Sha Tin'),
    ('2026-02-22', 'ST', 'Sunday - Sha Tin (complete, verify)'),
]

def scrape_date_gentle(pipeline, date_str, course, description):
    """Scrape a single date gently with delays."""
    logger.info(f"\n{'='*70}")
    logger.info(f"📅 Scraping {date_str} - {description}")
    logger.info(f"{'='*70}")
    
    total_saved = 0
    
    # Try both courses if unsure
    courses_to_try = [course]
    if course == 'ST':
        courses_to_try = ['ST', 'HV']  # Try Sha Tin first, then Happy Valley
    else:
        courses_to_try = ['HV', 'ST']  # Try Happy Valley first, then Sha Tin
    
    for try_course in courses_to_try:
        logger.info(f"\n  Trying course: {try_course}")
        
        # Scrape race cards first (for all races 1-12)
        logger.info(f"  📋 Scraping race cards...")
        cards_saved = 0
        for race_no in range(1, 13):
            try:
                count = pipeline.save_future_race_cards(date_str, try_course)
                if count > 0:
                    cards_saved += count
                    logger.info(f"    Race {race_no}: {count} horses")
                else:
                    # No more races for this course
                    if race_no > 8:
                        break
                
                # Gentle delay between race card requests
                time.sleep(1.5)
            except Exception as e:
                logger.warning(f"    Race {race_no}: {e}")
                time.sleep(2)
        
        if cards_saved > 0:
            logger.info(f"  ✅ Cards saved: {cards_saved}")
            total_saved += cards_saved
        
        # Gentle delay between cards and results
        time.sleep(2)
        
        # Scrape race results
        logger.info(f"  🏁 Scraping race results...")
        results_saved = 0
        for race_no in range(1, 13):
            try:
                count = pipeline.save_race_results(date_str, try_course)
                if count > 0:
                    results_saved += count
                    logger.info(f"    Race {race_no}: {count} results")
                else:
                    if race_no > 8:
                        break
                
                # Gentle delay between result requests
                time.sleep(1.5)
            except Exception as e:
                logger.warning(f"    Race {race_no}: {e}")
                time.sleep(2)
        
        if results_saved > 0:
            logger.info(f"  ✅ Results saved: {results_saved}")
            total_saved += results_saved
        
        # If we found data on this course, no need to try others
        if total_saved > 0:
            break
        
        # Delay before trying next course
        time.sleep(3)
    
    return total_saved

def main():
    logger.info("="*70)
    logger.info("🏇 GENTLE SCRAPER FOR FEBRUARY 12-22, 2026")
    logger.info("="*70)
    logger.info("This script will scrape with delays to avoid overloading the server.")
    logger.info("Delays: 1.5s between races, 2-3s between data types")
    logger.info("="*70)
    
    pipeline = HKJCDataPipeline()
    
    total_horses = 0
    successful_dates = []
    failed_dates = []
    
    for date_str, course, description in DATES_TO_SCRAPE:
        try:
            saved = scrape_date_gentle(pipeline, date_str, course, description)
            
            if saved > 0:
                total_horses += saved
                successful_dates.append(date_str)
                logger.info(f"✅ {date_str}: Successfully saved {saved} records")
            else:
                failed_dates.append(date_str)
                logger.info(f"⚠️ {date_str}: No data found")
            
            # Longer delay between dates
            logger.info(f"  ⏳ Waiting 5 seconds before next date...")
            time.sleep(5)
            
        except Exception as e:
            logger.error(f"❌ {date_str}: Failed with error: {e}")
            failed_dates.append(date_str)
            time.sleep(5)
    
    # Summary
    logger.info("\n" + "="*70)
    logger.info("📊 SCRAPING SUMMARY")
    logger.info("="*70)
    logger.info(f"Total records saved: {total_horses}")
    logger.info(f"Successful dates ({len(successful_dates)}): {', '.join(successful_dates)}")
    if failed_dates:
        logger.info(f"Failed/No data dates ({len(failed_dates)}): {', '.join(failed_dates)}")
    logger.info("="*70)

if __name__ == '__main__':
    main()
