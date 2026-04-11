#!/usr/bin/env python3
"""
Scrape race results for February 19, 2026
"""

import sys
import time
import logging

sys.path.insert(0, '.')

from scraper.pipeline import HKJCDataPipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("="*70)
    logger.info("🏇 SCRAPING FEBRUARY 19, 2026 RESULTS")
    logger.info("="*70)
    
    pipeline = HKJCDataPipeline()
    
    date_str = '2026-02-19'
    course = 'ST'
    
    total_saved = 0
    consecutive_empty = 0
    max_consecutive = 3
    
    logger.info(f"📅 Scraping results for {date_str} at {course}")
    
    for race_no in range(1, 13):
        try:
            count = pipeline.save_race_results(date_str, course)
            if count > 0:
                total_saved += count
                consecutive_empty = 0
                logger.info(f"  Race {race_no}: {count} results saved")
            else:
                consecutive_empty += 1
                logger.info(f"  Race {race_no}: No data (empty {consecutive_empty}/{max_consecutive})")
                if consecutive_empty >= max_consecutive:
                    logger.info(f"  Stopping - {max_consecutive} consecutive empty races")
                    break
            
            time.sleep(1.0)
        except Exception as e:
            logger.warning(f"  Race {race_no} error: {str(e)[:80]}")
            consecutive_empty += 1
            if consecutive_empty >= max_consecutive:
                break
            time.sleep(1.5)
    
    logger.info("="*70)
    logger.info(f"📊 TOTAL: {total_saved} results saved for {date_str}")
    logger.info("="*70)

if __name__ == '__main__':
    main()
