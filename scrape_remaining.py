#!/usr/bin/env python3
"""
Scrape remaining tables that need updating
- Rankings (jockey, trainer)
- Stats (JKC, TNC)
- Trackwork
- Weather
- Fixtures
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
    logger.info("🏇 SCRAPING REMAINING TABLES")
    logger.info("="*70)
    
    pipeline = HKJCDataPipeline()
    total_saved = 0
    
    # 1. Sync Rankings
    logger.info("\n📊 Syncing Jockey & Trainer Rankings...")
    try:
        rankings = pipeline.sync_all_rankings()
        logger.info(f"  ✅ Synced {rankings} ranking records")
        total_saved += rankings
    except Exception as e:
        logger.error(f"  ❌ Rankings error: {e}")
    
    time.sleep(2)
    
    # 2. JKC Stats
    logger.info("\n🏇 Scraping JKC Stats...")
    try:
        jkc = pipeline.save_jkc_stats()
        logger.info(f"  ✅ Saved {jkc} JKC records")
        total_saved += jkc
    except Exception as e:
        logger.error(f"  ❌ JKC error: {e}")
    
    time.sleep(2)
    
    # 3. TNC Stats
    logger.info("\n🐴 Scraping TNC Stats...")
    try:
        tnc = pipeline.save_tnc_stats()
        logger.info(f"  ✅ Saved {tnc} TNC records")
        total_saved += tnc
    except Exception as e:
        logger.error(f"  ❌ TNC error: {e}")
    
    time.sleep(2)
    
    # 4. Barrier Tests
    logger.info("\n🚧 Scraping Barrier Tests...")
    try:
        barrier = pipeline.save_barrier_tests()
        logger.info(f"  ✅ Saved {barrier} barrier test records")
        total_saved += barrier
    except Exception as e:
        logger.error(f"  ❌ Barrier tests error: {e}")
    
    time.sleep(2)
    
    # 5. Weather (for today)
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    logger.info(f"\n🌤️ Scraping Weather for {today}...")
    try:
        # Try both courses
        weather_st = pipeline.save_weather(today, 'ST')
        weather_hv = pipeline.save_weather(today, 'HV')
        weather_total = weather_st + weather_hv
        logger.info(f"  ✅ Saved {weather_total} weather records")
        total_saved += weather_total
    except Exception as e:
        logger.error(f"  ❌ Weather error: {e}")
    
    time.sleep(2)
    
    # 6. Fixtures (refresh)
    logger.info("\n📅 Refreshing Fixtures...")
    try:
        fixtures = pipeline.save_fixtures()
        logger.info(f"  ✅ Saved {fixtures} fixtures")
        total_saved += fixtures
    except Exception as e:
        logger.error(f"  ❌ Fixtures error: {e}")
    
    # Summary
    logger.info("\n" + "="*70)
    logger.info("📊 SCRAPING COMPLETE")
    logger.info("="*70)
    logger.info(f"Total records saved: {total_saved}")
    logger.info("\nSQL to check status:")
    logger.info("  sqlite3 database/hkjc_races.db \"SELECT 'jockey_rankings', COUNT(*), MAX(scraped_at) FROM jockey_rankings;\"")
    logger.info("  sqlite3 database/hkjc_races.db \"SELECT 'trainer_rankings', COUNT(*), MAX(scraped_at) FROM trainer_rankings;\"")
    logger.info("  sqlite3 database/hkjc_races.db \"SELECT 'jkc_stats', COUNT(*), MAX(scraped_at) FROM jkc_stats;\"")
    logger.info("  sqlite3 database/hkjc_races.db \"SELECT 'tnc_stats', COUNT(*), MAX(scraped_at) FROM tnc_stats;\"")
    logger.info("  sqlite3 database/hkjc_races.db \"SELECT 'weather', COUNT(*), MAX(scraped_at) FROM weather;\"")
    logger.info("="*70)

if __name__ == '__main__':
    main()
