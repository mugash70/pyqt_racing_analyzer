"""
Fixtures Browser - View and manage HKJC race fixtures
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QComboBox, QProgressBar, QTextEdit,
    QGroupBox, QSplitter, QMessageBox, QCalendarWidget, QListWidget,
    QListWidgetItem, QFrame
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QDate
from PyQt5.QtGui import QColor, QFont
import json
from datetime import datetime, timedelta


class FixturesScrapeWorker(QThread):
    """Worker thread for scraping fixtures"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, year=None, month=None):
        super().__init__()
        self.year = year or datetime.now().year
        self.month = month or datetime.now().month
        
    def run(self):
        try:
            from scraper.pipeline import HKJCDataPipeline
            
            self.progress.emit(f"Scraping fixtures for {self.year}-{self.month:02d}...")
            
            pipeline = HKJCDataPipeline()
            
            # Scrape fixtures
            count = pipeline.save_fixtures()
            
            result = {
                'status': 'success',
                'records': count,
                'year': self.year,
                'month': self.month
            }
            
            self.progress.emit(f"Scraped {count} fixtures")
            self.finished.emit(result)
            
        except Exception as e:
            self.error.emit(str(e))


class FixturesBrowser(QWidget):
    """Fixtures browser widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.scrape_worker = None
        self.init_ui()
        self.load_fixtures()
        
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header = QLabel("Race Fixtures Calendar")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #f8fafc; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Top controls
        controls = QHBoxLayout()
        
        # Month/Year selector
        self.month_combo = QComboBox()
        self.month_combo.addItems([
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ])
        self.month_combo.setCurrentIndex(datetime.now().month - 1)
        self.month_combo.currentIndexChanged.connect(self.on_month_changed)
        controls.addWidget(QLabel("Month:"))
        controls.addWidget(self.month_combo)
        
        self.year_combo = QComboBox()
        current_year = datetime.now().year
        for year in range(current_year - 1, current_year + 2):
            self.year_combo.addItem(str(year), year)
        self.year_combo.setCurrentIndex(1)  # Current year
        self.year_combo.currentIndexChanged.connect(self.on_month_changed)
        controls.addWidget(QLabel("Year:"))
        controls.addWidget(self.year_combo)
        
        controls.addSpacing(20)
        
        # Scrape button
        self.scrape_btn = QPushButton("🔄 Scrape Fixtures")
        self.scrape_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #1d4ed8; }
            QPushButton:disabled { background-color: #475569; }
        """)
        self.scrape_btn.clicked.connect(self.scrape_fixtures)
        controls.addWidget(self.scrape_btn)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #64748b;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #475569; }
        """)
        refresh_btn.clicked.connect(self.load_fixtures)
        controls.addWidget(refresh_btn)
        
        controls.addStretch()
        
        # Stats label
        self.stats_label = QLabel("No fixtures loaded")
        self.stats_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        controls.addWidget(self.stats_label)
        
        layout.addLayout(controls)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #334155;
                border-radius: 4px;
                background-color: #0f172a;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #3b82f6;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress)
        
        # Splitter for calendar and details
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side - Calendar view
        calendar_widget = QWidget()
        calendar_layout = QVBoxLayout(calendar_widget)
        calendar_layout.setContentsMargins(0, 0, 0, 0)
        
        calendar_header = QLabel("Calendar View")
        calendar_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #f8fafc;")
        calendar_layout.addWidget(calendar_header)
        
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setStyleSheet("""
            QCalendarWidget {
                background-color: #1e293b;
                color: #f8fafc;
            }
            QCalendarWidget QTableView {
                background-color: #0f172a;
                color: #f8fafc;
                selection-background-color: #2563eb;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: #1e293b;
            }
            QCalendarWidget QToolButton {
                color: #f8fafc;
                background-color: #334155;
                border: none;
                border-radius: 4px;
                padding: 4px;
            }
        """)
        self.calendar.clicked.connect(self.on_date_selected)
        calendar_layout.addWidget(self.calendar)
        
        # Race dates list
        race_dates_label = QLabel("Race Dates in Month:")
        race_dates_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #f8fafc; margin-top: 10px;")
        calendar_layout.addWidget(race_dates_label)
        
        self.race_dates_list = QListWidget()
        self.race_dates_list.setStyleSheet("""
            QListWidget {
                background-color: #0f172a;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 6px;
            }
            QListWidget::item:selected {
                background-color: #2563eb;
            }
            QListWidget::item:hover {
                background-color: #334155;
            }
        """)
        self.race_dates_list.itemClicked.connect(self.on_race_date_clicked)
        calendar_layout.addWidget(self.race_dates_list)
        
        splitter.addWidget(calendar_widget)
        
        # Right side - Details table
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.setContentsMargins(0, 0, 0, 0)
        
        details_header = QLabel("Fixture Details")
        details_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #f8fafc;")
        details_layout.addWidget(details_header)
        
        self.fixtures_table = QTableWidget()
        self.fixtures_table.setColumnCount(6)
        self.fixtures_table.setHorizontalHeaderLabels([
            "Date", "Course", "Day/Night", "Track", "Races", "Details"
        ])
        self.fixtures_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.fixtures_table.setStyleSheet("""
            QTableWidget {
                background-color: #0f172a;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 6px;
                gridline-color: #334155;
            }
            QHeaderView::section {
                background-color: #1e293b;
                color: #f8fafc;
                padding: 8px;
                border: 1px solid #334155;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #334155;
            }
            QTableWidget::item:selected {
                background-color: #2563eb;
            }
        """)
        self.fixtures_table.setAlternatingRowColors(True)
        self.fixtures_table.verticalHeader().setVisible(False)
        details_layout.addWidget(self.fixtures_table)
        
        # Selected date details
        self.date_details = QTextEdit()
        self.date_details.setReadOnly(True)
        self.date_details.setMaximumHeight(150)
        self.date_details.setStyleSheet("""
            QTextEdit {
                background-color: #0f172a;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 10px;
                font-family: monospace;
                font-size: 11px;
            }
        """)
        self.date_details.setPlaceholderText("Select a date to view race details...")
        details_layout.addWidget(self.date_details)
        
        splitter.addWidget(details_widget)
        splitter.setSizes([400, 600])
        
        layout.addWidget(splitter)
        
        # Log area
        log_group = QGroupBox("Activity Log")
        log_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(120)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #0f172a;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 8px;
                font-family: Monaco, Consolas, monospace;
                font-size: 11px;
            }
        """)
        log_layout.addWidget(self.log_text)
        layout.addWidget(log_group)
        
    def log(self, message):
        """Add log message"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
    def load_fixtures(self):
        """Load fixtures from database"""
        try:
            import sqlite3
            import os
            
            db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'hkjc_races.db')
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if fixtures table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fixtures'")
            if not cursor.fetchone():
                self.log("Fixtures table does not exist yet. Please scrape fixtures first.")
                conn.close()
                return
            
            # Get all fixtures
            cursor.execute("""
                SELECT race_date, racecourse, day_night, track_type, race_count, races_json
                FROM fixtures
                ORDER BY race_date DESC
            """)
            
            fixtures = cursor.fetchall()
            conn.close()
            
            if not fixtures:
                self.log("No fixtures found in database. Please scrape fixtures.")
                self.stats_label.setText("No fixtures in database")
                return
            
            self.all_fixtures = fixtures  # Store all fixtures for filtering
            self.populate_table(fixtures)
            self.populate_race_dates(fixtures)
            self.highlight_race_dates(fixtures)
            
            # Count fixtures for selected month
            current_month = self.month_combo.currentIndex() + 1
            current_year = int(self.year_combo.currentText())
            month_count = sum(1 for f in fixtures if datetime.strptime(f[0], "%Y-%m-%d").month == current_month and datetime.strptime(f[0], "%Y-%m-%d").year == current_year)
            
            self.stats_label.setText(f"Showing {month_count} of {len(fixtures)} total fixtures")
            self.log(f"Loaded {len(fixtures)} fixtures from database ({month_count} for selected month)")
            
        except Exception as e:
            self.log(f"Error loading fixtures: {e}")
        
    def populate_table(self, fixtures):
        """Populate the fixtures table with filtered data for selected month/year"""
        # Filter fixtures by selected month and year
        current_month = self.month_combo.currentIndex() + 1
        current_year = int(self.year_combo.currentText())
        
        filtered_fixtures = []
        for fixture in fixtures:
            race_date = fixture[0] if isinstance(fixture, tuple) else fixture.get('race_date')
            try:
                date_obj = datetime.strptime(race_date, "%Y-%m-%d")
                if date_obj.month == current_month and date_obj.year == current_year:
                    filtered_fixtures.append(fixture)
            except:
                continue
        
        self.fixtures_table.setRowCount(len(filtered_fixtures))
        
        for i, (race_date, racecourse, day_night, track_type, race_count, races_json) in enumerate(filtered_fixtures):
            # Date
            date_item = QTableWidgetItem(race_date)
            date_item.setData(Qt.UserRole, race_date)
            self.fixtures_table.setItem(i, 0, date_item)
            
            # Course
            course_text = racecourse if racecourse else "Unknown"
            self.fixtures_table.setItem(i, 1, QTableWidgetItem(course_text))
            
            # Day/Night
            dn_text = day_night if day_night else "Unknown"
            self.fixtures_table.setItem(i, 2, QTableWidgetItem(dn_text))
            
            # Track
            track_text = track_type if track_type else "Unknown"
            self.fixtures_table.setItem(i, 3, QTableWidgetItem(track_text))
            
            # Races count
            self.fixtures_table.setItem(i, 4, QTableWidgetItem(str(race_count)))
            
            # Details summary
            try:
                races = json.loads(races_json) if races_json else []
                details = f"{len(races)} races"
                if races:
                    classes = [r.get('class', '') for r in races if r.get('class')]
                    if classes:
                        details += f" (Classes: {', '.join(set(classes))})"
            except:
                details = "No details"
            
            self.fixtures_table.setItem(i, 5, QTableWidgetItem(details))
            
    def populate_race_dates(self, fixtures):
        """Populate the race dates list"""
        self.race_dates_list.clear()
        
        current_month = self.month_combo.currentIndex() + 1
        current_year = int(self.year_combo.currentText())
        
        for race_date, racecourse, day_night, track_type, race_count, _ in fixtures:
            try:
                date_obj = datetime.strptime(race_date, "%Y-%m-%d")
                if date_obj.month == current_month and date_obj.year == current_year:
                    item_text = f"{race_date} - {racecourse} ({day_night}) - {race_count} races"
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.UserRole, race_date)
                    self.race_dates_list.addItem(item)
            except:
                continue
                
    def highlight_race_dates(self, fixtures):
        """Highlight race dates in calendar"""
        # Store race dates for highlighting
        self.race_dates = set()
        for race_date, _, _, _, _, _ in fixtures:
            try:
                date_obj = datetime.strptime(race_date, "%Y-%m-%d")
                self.race_dates.add(date_obj.toordinal())
            except:
                continue
        
        # Calendar doesn't support direct date highlighting, but we can use the paintCell method
        # For now, we'll rely on the race_dates_list
        
    def on_month_changed(self):
        """Handle month/year change"""
        month = self.month_combo.currentIndex() + 1
        year = int(self.year_combo.currentText())
        
        # Update calendar
        self.calendar.setSelectedDate(QDate(year, month, 1))
        
        # Reload race dates for this month
        self.load_fixtures()
        
    def on_date_selected(self, date):
        """Handle calendar date selection"""
        date_str = date.toString("yyyy-MM-dd")
        self.show_date_details(date_str)
        
    def on_race_date_clicked(self, item):
        """Handle race date list item click"""
        date_str = item.data(Qt.UserRole)
        self.show_date_details(date_str)
        
    def show_date_details(self, date_str):
        """Show details for a specific date"""
        try:
            import sqlite3
            import os
            
            db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'hkjc_races.db')
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT race_date, racecourse, day_night, track_type, race_count, races_json
                FROM fixtures
                WHERE race_date = ?
            """, (date_str,))
            
            fixture = cursor.fetchone()
            conn.close()
            
            if not fixture:
                self.date_details.setText(f"No fixture data for {date_str}")
                return
            
            race_date, racecourse, day_night, track_type, race_count, races_json = fixture
            
            details = f"Date: {race_date}\n"
            details += f"Racecourse: {racecourse or 'Unknown'}\n"
            details += f"Day/Night: {day_night or 'Unknown'}\n"
            details += f"Track Type: {track_type or 'Unknown'}\n"
            details += f"Total Races: {race_count}\n"
            details += "-" * 40 + "\n"
            
            try:
                races = json.loads(races_json) if races_json else []
                for i, race in enumerate(races, 1):
                    race_class = race.get('class', 'Unknown')
                    race_details = race.get('details', '')
                    details += f"Race {i}: Class {race_class} - {race_details}\n"
            except:
                details += "Could not parse race details\n"
            
            self.date_details.setText(details)
            
        except Exception as e:
            self.date_details.setText(f"Error loading details: {e}")
            
    def scrape_fixtures(self):
        """Scrape fixtures from HKJC"""
        self.scrape_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)  # Indeterminate
        
        self.log("Starting fixtures scrape...")
        
        year = int(self.year_combo.currentText())
        month = self.month_combo.currentIndex() + 1
        
        self.scrape_worker = FixturesScrapeWorker(year, month)
        self.scrape_worker.progress.connect(self.log)
        self.scrape_worker.finished.connect(self.on_scrape_finished)
        self.scrape_worker.error.connect(self.on_scrape_error)
        self.scrape_worker.start()
        
    def on_scrape_finished(self, result):
        """Handle scrape completion"""
        self.scrape_btn.setEnabled(True)
        self.progress.setVisible(False)
        
        records = result.get('records', 0)
        self.log(f"Scraped {records} fixtures successfully")
        
        QMessageBox.information(self, "Success", f"Scraped {records} fixtures!")
        
        # Reload fixtures
        self.load_fixtures()
        
    def on_scrape_error(self, error):
        """Handle scrape error"""
        self.scrape_btn.setEnabled(True)
        self.progress.setVisible(False)
        
        self.log(f"Error scraping fixtures: {error}")
        QMessageBox.critical(self, "Error", f"Failed to scrape fixtures:\n{error}")
