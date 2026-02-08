"""
Data Refresh Worker - Background thread for scraping new race data
"""

from PyQt5.QtCore import QThread, pyqtSignal
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timedelta
import logging

class DataRefreshWorker(QThread):
    """Worker thread for data scraping operations"""
    
    progress = pyqtSignal(str)  # Progress message
    stage_changed = pyqtSignal(str)  # Current stage
    races_scraped = pyqtSignal(int)  # Number of races scraped
    data_appended = pyqtSignal(dict)  # Data appended signal
    finished = pyqtSignal(dict)  # Final results
    error = pyqtSignal(str)  # Error message
    
    def __init__(self, lookback_days: int = 7):
        super().__init__()
        self.lookback_days = lookback_days
        self.logger = logging.getLogger(__name__)
        
    def run(self):
        """Execute the data refresh pipeline"""
        try:
            results = {
                'dates_processed': 0,
                'races_scraped': 0,
                'races_updated': 0,
                'errors': [],
                'start_time': datetime.now()
            }
            
            # Import pipeline components
            from backup_scraper.pipeline import HKJCDataPipeline
            from backup_scraper.scraper import HKJCResultsScraper
            
            self.progress.emit("Initializing data pipeline...")
            self.stage_changed.emit("initializing")
            
            pipeline = HKJCDataPipeline()
            scraper = HKJCResultsScraper()
            
            # Get available dates
            self.progress.emit("Fetching available dates from HKJC...")
            self.stage_changed.emit("fetching_dates")
            
            available_dates = scraper.get_available_dates()
            self.progress.emit(f"Found {len(available_dates)} available dates")
            
            # Filter dates within lookback period
            cutoff_date = datetime.now() - timedelta(days=self.lookback_days)
            dates_to_scrape = [d for d in available_dates if d >= cutoff_date]
            
            self.progress.emit(f"Processing {len(dates_to_scrape)} dates (last {self.lookback_days} days)")
            results['dates_processed'] = len(dates_to_scrape)
            
            total_races = 0
            updated_races = 0
            
            for i, race_date in enumerate(dates_to_scrape):
                try:
                    date_str = race_date.strftime("%Y-%m-%d")
                    self.progress.emit(f"Scraping data for {date_str}...")
                    self.stage_changed.emit(f"scraping_{date_str}")
                    
                    # Check if date already scraped
                    if pipeline._date_already_scraped(race_date):
                        self.progress.emit(f"  Data for {date_str} already exists, skipping...")
                        continue
                    
                    # Scrape races for this date
                    races = scraper.parse_results_page(race_date)
                    
                    races_saved = 0
                    for race in races:
                        if pipeline.save_race_data(race):
                            races_saved += 1
                            total_races += 1
                            
                            # Emit signal for each race appended
                            self.data_appended.emit({
                                'date': date_str,
                                'race_number': race.get('race_number'),
                                'distance': race.get('distance'),
                                'horse_count': len(race.get('positions', []))
                            })
                    
                    updated_races = races_saved
                    self.races_scraped.emit(total_races)
                    
                    self.progress.emit(f"  Saved {races_saved} races from {date_str}")
                    
                    # Rate limiting
                    self.msleep(500)
                    
                except Exception as e:
                    error_msg = f"Error processing {race_date}: {str(e)}"
                    self.logger.error(error_msg)
                    results['errors'].append(error_msg)
                    self.progress.emit(f"  ERROR: {error_msg}")
            
            results['races_scraped'] = total_races
            results['races_updated'] = updated_races
            results['end_time'] = datetime.now()
            results['duration_seconds'] = (results['end_time'] - results['start_time']).total_seconds()
            
            self.progress.emit(f"Data refresh complete! Scraped {total_races} races in {results['duration_seconds']:.1f} seconds")
            self.stage_changed.emit("completed")
            self.finished.emit(results)
            
        except Exception as e:
            error_msg = f"Fatal error in data refresh: {str(e)}"
            self.logger.error(error_msg)
            self.error.emit(error_msg)

    def stop(self):
        """Stop the worker thread"""
        self.terminate()
        self.wait()
