#!/usr/bin/env python3
"""
Efficient scraper for February 2026 race dates only.
Focuses on known race dates: Feb 14, 19, 22
Non-aggressive scraping with delays between requests.
"""

import sys
import time
import logging
from datetime import datetime

sys.path.insert(0, '.')

from scraper.pipeline import HKJCDataPipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Only known race dates based on existing fixtures data
# Feb 14 = Saturday (CNY meeting at Sha Tin)
# Feb 19 = Thursday (Sha Tin)
# Feb 22 = Sunday (Sha Tin)
RACE_DATES = [
    ('2026-02-14', 'ST', 'Saturday - CNY meeting at Sha Tin'),
    ('2026-02-19', 'ST', 'Thursday - Sha Tin (has cards, needs results)'),
    ('2026-02-22', 'ST', 'Sunday - Sha Tin (verify/complete)'),
]

def scrape_date_efficient(pipeline, date_str, course, description):
    """Scrape a single date efficiently with early stopping."""
    logger.info(f"\n{'='*70}")
    logger.info(f"📅 Scraping {date_str} - {description}")
    logger.info(f"{'='*70}")
    
    total_saved = 0
    
    # Scrape race cards first (stop after 3 consecutive empty races)
    logger.info(f"📋 Scraping race cards...")
    cards_saved = 0
    consecutive_empty = 0
    max_consecutive = 3
    
    for race_no in range(1, 13):
        try:
            count = pipeline.save_future_race_cards(date_str, course)
            if count > 0:
                cards_saved += count
                consecutive_empty = 0
                logger.info(f"  Race {race_no}: {count} horses saved")
            else:
                consecutive_empty += 1
                logger.info(f"  Race {race_no}: No data (empty {consecutive_empty}/{max_consecutive})")
                if consecutive_empty >= max_consecutive:
                    logger.info(f"  Stopping cards - {max_consecutive} consecutive empty races")
                    break
            
            # Gentle delay between race card requests
            time.sleep(1.0)
        except Exception as e:
            logger.warning(f"  Race {race_no} error: {str(e)[:60]}")
            consecutive_empty += 1
            if consecutive_empty >= max_consecutive:
                break
            time.sleep(1.5)
    
    if cards_saved > 0:
        logger.info(f"✅ Total cards saved: {cards_saved}")
        total_saved += cards_saved
    else:
        logger.info(f"⚠️ No race cards found")
    
    # Delay between cards and results
    time.sleep(2)
    
    # Scrape race results
    logger.info(f"🏁 Scraping race results...")
    results_saved = 0
    consecutive_empty = 0
    
    for race_no in range(1, 13):
        try:
            count = pipeline.save_race_results(date_str, course)
            if count > 0:
                results_saved += count
                consecutive_empty = 0
                logger.info(f"  Race {race_no}: {count} results saved")
            else:
                consecutive_empty += 1
                logger.info(f"  Race {race_no}: No data (empty {consecutive_empty}/{max_consecutive})")
                if consecutive_empty >= max_consecutive:
                    logger.info(f"  Stopping results - {max_consecutive} consecutive empty races")
                    break
            
            # Gentle delay between result requests
            time.sleep(1.0)
        except Exception as e:
            logger.warning(f"  Race {race_no} error: {str(e)[:60]}")
            consecutive_empty += 1
            if consecutive_empty >= max_consecutive:
                break
            time.sleep(1.5)
    
    if results_saved > 0:
        logger.info(f"✅ Total results saved: {results_saved}")
        total_saved += results_saved
    else:
        logger.info(f"⚠️ No race results found")
    
    return total_saved

def main():
    logger.info("="*70)
    logger.info("🏇 EFFICIENT SCRAPER FOR FEBRUARY 2026 RACE DATES")
    logger.info("="*70)
    logger.info("Focusing on known race dates: Feb 14, 19, 22")
    logger.info("Early stopping after 3 consecutive empty races")
    logger.info("Delays: 1s between races, 2s between data types")
    logger.info("="*70)
    
    pipeline = HKJCDataPipeline()
    
    total_horses = 0
    successful_dates = []
    
    for date_str, course, description in RACE_DATES:
        try:
            saved = scrape_date_efficient(pipeline, date_str, course, description)
            
            if saved > 0:
                total_horses += saved
                successful_dates.append(f"{date_str} ({saved} records)")
                logger.info(f"\n✅ {date_str}: Successfully saved {saved} records")
            else:
                logger.info(f"\n⚠️ {date_str}: No data found")
            
            # Delay between dates
            if date_str != RACE_DATES[-1][0]:  # Don't delay after last date
                logger.info(f"⏳ Waiting 5 seconds before next date...")
                time.sleep(5)
            
        except Exception as e:
            logger.error(f"\n❌ {date_str}: Failed with error: {e}")
            time.sleep(5)
    
    # Summary
    logger.info("\n" + "="*70)
    logger.info("📊 SCRAPING SUMMARY")
    logger.info("="*70)
    logger.info(f"Total records saved: {total_horses}")
    if successful_dates:
        logger.info(f"Successful dates: {', '.join(successful_dates)}")
    logger.info("="*70)

if __name__ == '__main__':
    main()
