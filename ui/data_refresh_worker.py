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
            from scraper.pipeline import HKJCDataPipeline
            from scraper.scraper import HKJCResultsScraper
            
            self.progress.emit("Initializing data pipeline...")
            self.stage_changed.emit("initializing")
            
            pipeline = HKJCDataPipeline()
            scraper = HKJCResultsScraper()
            
            # Generate dates to scrape (last N days)
            self.progress.emit(f"Generating dates for last {self.lookback_days} days...")
            self.stage_changed.emit("fetching_dates")
            
            # Generate dates from today going back lookback_days
            dates_to_scrape = []
            for i in range(self.lookback_days):
                date = datetime.now() - timedelta(days=i)
                # Only include Wednesdays and weekends (typical race days)
                if date.weekday() in [2, 5, 6]:  # Wed=2, Sat=5, Sun=6
                    dates_to_scrape.append(date)
            
            self.progress.emit(f"Found {len(dates_to_scrape)} potential race dates")
            results['dates_processed'] = len(dates_to_scrape)
            
            total_races = 0
            
            # Try both racecourses
            racecourses = ["ST", "HV"]
            
            for race_date in dates_to_scrape:
                date_str = race_date.strftime("%Y-%m-%d")
                self.progress.emit(f"Scraping data for {date_str}...")
                self.stage_changed.emit(f"scraping_{date_str}")
                
                for racecourse in racecourses:
                    try:
                        # Scrape race results for this date and course
                        records = pipeline.save_race_results(date_str, racecourse)
                        
                        if records > 0:
                            total_races += records
                            self.races_scraped.emit(total_races)
                            self.progress.emit(f"  Saved {records} records from {date_str} at {racecourse}")
                            
                            # Also try to scrape race cards and weather
                            try:
                                pipeline.save_future_race_cards(date_str, racecourse)
                            except Exception:
                                pass
                            try:
                                pipeline.save_weather(date_str, racecourse)
                            except Exception:
                                pass
                        
                        # Rate limiting between courses
                        self.msleep(200)
                        
                    except Exception as e:
                        error_msg = f"Error scraping {date_str} at {racecourse}: {str(e)}"
                        self.logger.error(error_msg)
                        results['errors'].append(error_msg)
                        self.progress.emit(f"  ERROR: {error_msg}")
                
                # Rate limiting between dates
                self.msleep(500)
            
            # Also sync general data that doesn't depend on dates
            self.progress.emit("Syncing general rankings and stats...")
            self.stage_changed.emit("syncing_general")
            try:
                rankings = pipeline.sync_all_rankings()
                self.progress.emit(f"  Synced {rankings} ranking records")
            except Exception as e:
                self.progress.emit(f"  Warning: Could not sync rankings: {e}")
            
            results['races_scraped'] = total_races
            results['end_time'] = datetime.now()
            results['duration_seconds'] = (results['end_time'] - results['start_time']).total_seconds()
            
            self.progress.emit(f"Data refresh complete! Scraped {total_races} race records in {results['duration_seconds']:.1f} seconds")
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
