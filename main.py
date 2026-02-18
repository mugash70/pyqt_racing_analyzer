#!/usr/bin/env python3
"""
HKJC Racing Intelligence Terminal - Professional Betting Workstation
Modern PyQt6 application with animated loading and professional UI
"""

import sys
import os
import logging
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QFrame, QStackedWidget, QProgressBar, QPushButton, QListWidget, QListWidgetItem, QGridLayout, QComboBox
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QSize, QDateTime, QTranslator
from PyQt5.QtGui import QFont, QIcon, QColor, QPixmap

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hkjc_terminal.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

try:
    from .ui.styles import COLORS, APP_STYLESHEET
    from .ui.loading_screen import LoadingScreen
    from .ui.home_page import HomePage
    from .ui.home_page_redesign import RedesignedHomePage
    from .ui.database_browser import DatabaseBrowser
    from .ui.settings_tab import SettingsTab
    from .ui.analysis_tab import AnalysisTab
    from .ui.retraining_dialog import RetrainingDialog
    from .ui.prediction_detail_modal import RacePredictionModal
    from .ui.prediction_dashboard import PredictionDetailModal
except ImportError:
    from ui.styles import COLORS, APP_STYLESHEET
    from ui.loading_screen import LoadingScreen
    from ui.home_page import HomePage
    from ui.home_page_redesign import RedesignedHomePage
    from ui.database_browser import DatabaseBrowser
    from ui.settings_tab import SettingsTab
    from ui.analysis_tab import AnalysisTab
    from ui.retraining_dialog import RetrainingDialog
    from ui.prediction_detail_modal import RacePredictionModal
    from ui.prediction_dashboard import PredictionDetailModal


class DataLoadingWorker(QThread):
    """Background worker for data pipeline initialization"""

    progress_update = pyqtSignal(str, int)  # message, percentage
    loading_complete = pyqtSignal()
    loading_error = pyqtSignal(str)

    def __init__(self, racecourse="ST"):
        super().__init__()
        self.pipeline = None
        self.racecourse = racecourse

    def run(self):
        """Execute the complete data loading pipeline"""
        try:
            import sys
            import os
            # Add parent directory to path for imports
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sys.path.insert(0, parent_dir)

            from scraper.pipeline import HKJCDataPipeline
            from datetime import datetime
            import sqlite3

            self.progress_update.emit("初始化數據管道...", 5)

            # Initialize pipeline
            self.pipeline = HKJCDataPipeline()
            today = datetime.now()
            today_str = today.strftime("%Y-%m-%d")
            
            # Check if data already exists for today
            def data_exists_for_today(table_name):
                try:
                    conn = sqlite3.connect(self.pipeline.db_path)
                    cursor = conn.cursor()
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE (DATE(race_date) = ? OR DATE(scraped_at) = ?) AND racecourse = ?", (today_str, today_str, self.racecourse))
                    count = cursor.fetchone()[0]
                    conn.close()
                    return count > 0
                except:
                    return False

            # Standard Times
            self.progress_update.emit("更新標準時間...", 10)
            self.pipeline.save_standard_times()
            
            # Fixtures
            self.progress_update.emit("更新賽事安排...", 15)
            self.pipeline.save_fixtures()
            
            # Barrier Tests
            self.progress_update.emit("更新閘位測試結果...", 20)
            self.pipeline.save_barrier_tests()
            
            # Future Race Cards
            self.progress_update.emit("加載未來賽程...", 25)
            if not data_exists_for_today('future_race_cards'):
                records = self.pipeline.save_future_race_cards(today, self.racecourse)
            else:
                records = 0
            logger.info(f"Loaded {records} future race cards")

            # Weather Data
            self.progress_update.emit("獲取天氣數據...", 40)
            if not data_exists_for_today('weather'):
                records = self.pipeline.save_weather(today, self.racecourse)
            else:
                records = 0
            logger.info(f"Loaded weather data: {records} records")

        
            self.progress_update.emit("Processing Form Lines...", 60)
            if not data_exists_for_today('form_line'):
                records = self.pipeline.save_form_line(today, self.racecourse)
            else:
                records = 0
            logger.info(f"Loaded form lines: {records} records")


            self.progress_update.emit("加載賽事結果...", 80)
            if not data_exists_for_today('race_results'):
                records = self.pipeline.save_race_results(today, self.racecourse)
            else:
                records = 0
            logger.info(f"Loaded race results: {records} records")

        
            self.progress_update.emit("連接即時賠率...", 85)
            total_odds = 0
            for race_number in range(1, 12):
                records = self.pipeline.save_live_odds(today_str, race_number, self.racecourse)
                total_odds += records
            logger.info(f"Loaded live odds: {total_odds} records")
            
            # Additional high-value data points
            self.progress_update.emit("獲取上賽摘要...", 87)
            self.pipeline.save_last_race_summaries(today)
            
            self.progress_update.emit("獲取專業日程...", 89)
            self.pipeline.sync_professional_schedules(today_str)
            
            self.progress_update.emit("更新馬鞍與閘位統計...", 91)
            self.pipeline.save_barrier_stats_v2()
            
            self.progress_update.emit("獲取風速數據...", 93)
            self.pipeline.save_wind_tracker(today)
            
            self.progress_update.emit("更新賽事備忘錄...", 95)
            self.pipeline.save_battle_memorandum()
            
            self.progress_update.emit("獲取新馬介紹...", 97)
            self.pipeline.save_new_horse_introductions()
            
            # Add new components
            self.progress_update.emit("更新練馬師赔率...", 98)
            self.pipeline.update_trainer_king_odds(today_str)
            
            self.progress_update.emit("更新賽日變更...", 99)
            self.pipeline.update_race_day_changes(today_str)
            
            self.progress_update.emit("更新賽道選擇數據...", 100)
            self.pipeline.update_track_selection(today_str)
            
            self.progress_update.emit("更新受傷記錄...", 100)
            self.pipeline.save_injury_records_v2()
            
            self.progress_update.emit("數據加載完成", 100)
            self.loading_complete.emit()

        except Exception as e:
            error_msg = f"數據加載失敗: {str(e)}"
            logger.error(error_msg)
            self.loading_error.emit(error_msg)


class ClickableRaceCard(QFrame):
    """Clickable race card widget"""
    race_clicked = pyqtSignal(str, int)
    
    def __init__(self, race_date: str, race_num: int, race_name: str, time: str, venue: str, parent=None):
        super().__init__(parent)
        self.race_date = race_date
        self.race_num = race_num
        self.setFixedHeight(80)
        self.setObjectName("statCard")
        self.setCursor(Qt.PointingHandCursor)
        
        self.setStyleSheet("""
            QFrame#statCard {
                background-color: #161b22;
                border: 2px solid #30363d;
                border-radius: 1px;
            }
            QFrame:hover {
                border-color: #58a6ff;
                background-color: #1c2128;
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        race_label = QLabel(f"<b>{race_name}</b> • {time}")
        race_label.setStyleSheet("""
            font-size: 13px;
            color: #c9d1d9;
        """)
        info_layout.addWidget(race_label)
        
        venue_label = QLabel(f"{venue}")
        venue_label.setStyleSheet("""
            font-size: 11px;
            color: #8b949e;
        """)
        info_layout.addWidget(venue_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
    
    def mousePressEvent(self, event):
        """Emit signal on click"""
        self.race_clicked.emit(self.race_date, self.race_num)


class MainWindow(QMainWindow):
    """Modern professional betting intelligence terminal - Complete """

    def __init__(self):
        super().__init__()
        self.translator = QTranslator()
        
        # Set default language to Traditional Chinese (繁體中文)
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "i18n", "zh_HK.qm")
        if os.path.exists(path) and self.translator.load(path):
            QApplication.installTranslator(self.translator)
            logger.info("Default language set to Traditional Chinese")
        
        self.setWindowTitle(self.tr("Mr. Chan Exclusive Edition"))
        self.selected_date = None  # Will be set by date dropdown

        # Dynamic window sizing based on screen resolution
        # self._set_dynamic_window_size()
        self.setGeometry(100, 100, 1600, 950)
        self.setMinimumSize(1366, 800)

        # UI Mode: "original" or "redesigned"
        self.ui_mode = "redesigned"

        # Dark theme with accent colors (terminal style)
        self.setStyleSheet(self._get_terminal_stylesheet())

        # Main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top bar - Ultra minimal
        self.top_bar = self._create_top_bar()
        main_layout.addWidget(self.top_bar)

        # Main content area with sidebar
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Left sidebar - Navigation
        self.sidebar = self._create_sidebar()
        content_layout.addWidget(self.sidebar)

        # Main content stack
        self.content_stack = QStackedWidget()
        content_layout.addWidget(self.content_stack, 1)
        main_layout.addWidget(content_widget, 1)

        # Bottom status bar
        status_bar = self._create_status_bar()
        main_layout.addWidget(status_bar)

        # Create pages
        self._create_pages()
        
        # Set initial page
        self.sidebar.setCurrentRow(0)
        self._switch_page(0)
        
        # Apply new UI settings (hide top bar controls since new UI has its own)
        self._set_top_bar_visible(False)

    def _get_terminal_stylesheet(self):
        """Terminal-inspired dark theme"""
        return """
            QMainWindow {
                background-color: #0d1117;
            }
            
            QWidget {
                font-family: Arial;
                color: #c9d1d9;
            }
            
            QListWidget {
                background-color: #161b22;
                border: none;
                outline: none;
                font-size: 12px;
            }
            
            QListWidget::item {
                padding: 12px 16px;
                border-left: 3px solid transparent;
            }
            
            QListWidget::item:selected {
                background-color: #1c2128;
                border-left: 3px solid #58a6ff;
                color: #ffffff;
            }
            
            QListWidget::item:hover {
                background-color: #1c2128;
            }
            
            QLabel {
                color: #c9d1d9;
                border: none;
                background-color: transparent;
                outline: none;
            }
            
            QFrame {
                background-color: transparent;
            }
        """

    def _create_top_bar(self):
        """Ultra minimal top bar"""
        top_bar = QFrame()
        top_bar.setFixedHeight(40)
        top_bar.setStyleSheet("""
            QFrame {
                background-color: #161b22;
                border-bottom: 1px solid #30363d;
            }
        """)

        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(20)

        # Logo/Title
        self.title_label = QLabel(self.tr("Mr. Chan Exclusive Edition"))
        self.title_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #58a6ff;
            letter-spacing: 1px;
        """)
        layout.addWidget(self.title_label)

        # Date dropdown
        date_layout = QHBoxLayout()
        date_layout.setSpacing(8)

        # Racecourse dropdown
        self.course_label = QLabel(self.tr("Course:"))
        self.course_label.setStyleSheet("color: #cbd5e1; font-size: 11px;")
        date_layout.addWidget(self.course_label)

        self.course_dropdown = QComboBox()
        self.course_dropdown.addItems(["ST", "HV"])
        self.course_dropdown.setStyleSheet("""
            QComboBox {
                background-color: #0f172a;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
                min-width: 60px;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        date_layout.addWidget(self.course_dropdown)

        self.date_label = QLabel(self.tr("Date:"))
        self.date_label.setStyleSheet("color: #cbd5e1; font-size: 11px;")
        date_layout.addWidget(self.date_label)

        self.date_dropdown = QComboBox()
        self.date_dropdown.setStyleSheet("""
            QComboBox {
                background-color: #0f172a;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
                min-width: 120px;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        self._populate_date_dropdown()
        date_layout.addWidget(self.date_dropdown)

        # Apply button
        self.apply_btn = QPushButton(self.tr("Apply"))
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #238636;
                color: #f8fafc;
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2ea043;
            }
            QPushButton:pressed {
                background-color: #1a7f37;
            }
        """)
        self.apply_btn.clicked.connect(self._apply_selected_date)
        date_layout.addWidget(self.apply_btn)

        layout.addLayout(date_layout)

        layout.addStretch()

        # Quick actions
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)

        # Refresh button
        self.refresh_btn = self._create_icon_button("↻", "#58a6ff")
        self.refresh_btn.setToolTip(self.tr("Refresh Data"))
        self.refresh_btn.clicked.connect(self._refresh_data)
        actions_layout.addWidget(self.refresh_btn)

        # Retrain button
        self.retrain_btn = self._create_icon_button("⚡", "#f59e0b")
        self.retrain_btn.setToolTip(self.tr("Retrain Models"))
        self.retrain_btn.clicked.connect(self._show_retraining_dialog)
        actions_layout.addWidget(self.retrain_btn)

        # Settings button
        settings_btn = self._create_icon_button("⚙", "#8b949e")
        settings_btn.setToolTip(self.tr("Settings"))
        actions_layout.addWidget(settings_btn)

        # UI Mode Switch button
        self.ui_mode_btn = QPushButton(self.tr("Old UI"))
        self.ui_mode_btn.setFixedSize(70, 28)
        self.ui_mode_btn.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: #f8fafc;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #047857;
            }
        """)
        self.ui_mode_btn.clicked.connect(self._toggle_ui_mode)
        actions_layout.addWidget(self.ui_mode_btn)

        layout.addLayout(actions_layout)

        return top_bar
    
    def _create_icon_button(self, icon, color):
        """Create a minimal icon button"""
        btn = QPushButton(icon)
        btn.setFixedSize(28, 28)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid #30363d;
                border-radius: 4px;
                color: {color};
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: #1c2128;
                border-color: #58a6ff;
            }}
        """)
        return btn

    def _create_sidebar(self):
        """Modern sidebar navigation"""
        sidebar = QListWidget()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("""
            QListWidget {
                background-color: #161b22;
                border: none;
                border-right: 1px solid #30363d;
            }
        """)
        
        # Navigation items
        self.nav_items_map = {}
        nav_items = [
            ("DASHBOARD", "overview"),
            ("ANALYTICS", "analytics"),
            ("DATABASE", "database"),
            ("SETTINGS", "settings")
        ]
        
        for text_key, icon_type in nav_items:
            item = QListWidgetItem(self.tr(text_key))
            item.setData(Qt.UserRole, icon_type)
            item.setSizeHint(QSize(220, 48))
            sidebar.addItem(item)
            self.nav_items_map[text_key] = item
        
        
        sidebar.currentRowChanged.connect(self._switch_page)
        return sidebar

    def _create_status_bar(self):
        """Minimal status bar"""
        status_bar = QFrame()
        status_bar.setFixedHeight(32)
        status_bar.setStyleSheet("""
            QFrame {
                background-color: #161b22;
                border-top: 1px solid #30363d;
            }
        """)
        
        layout = QHBoxLayout(status_bar)
        layout.setContentsMargins(16, 0, 16, 0)
        
        # Status indicator
        status_indicator = QLabel("●")
        status_indicator.setStyleSheet("""
            color: #238636;
            font-size: 10px;
        """)
        layout.addWidget(status_indicator)
        
        self.status_label = QLabel(self.tr("LIVE"))
        self.status_label.setStyleSheet("""
            color: #8b949e;
            font-size: 11px;
            font-weight: bold;
        """)
        layout.addWidget(self.status_label)
        
        layout.addSpacing(20)
        
        # Connection status
        self.db_status_label = QLabel(self.tr("DB: CONNECTED"))
        self.db_status_label.setStyleSheet("""
            color: #8b949e;
            font-size: 11px;
        """)
        layout.addWidget(self.db_status_label)
        
        layout.addStretch()
        
        # Time
        self.time_label = QLabel()
        self.time_label.setStyleSheet("""
            color: #8b949e;
            font-size: 11px;
        """)
        layout.addWidget(self.time_label)
        
        # Update timer
        self._update_time()
        timer = QTimer(self)
        timer.timeout.connect(self._update_time)
        timer.start(1000)
        
        return status_bar

    def _update_time(self):
        """Update time in status bar"""
        current_time = QDateTime.currentDateTime().toString("hh:mm:ss AP")
        self.time_label.setText(current_time)

    def _set_dynamic_window_size(self):
        """Set window size dynamically based on screen resolution"""
        try:
            # Get available screen geometry
            screen = QApplication.desktop().availableGeometry()
            screen_width = screen.width()
            screen_height = screen.height()

            # Calculate optimal window size (80% of screen, max reasonable size)
            max_width = min(int(screen_width * 0.8), 1800)   # Max 1800px wide
            max_height = min(int(screen_height * 0.8), 1000) # Max 1000px tall

            # Set minimum sizes (reasonable minimums)
            min_width = min(1200, max_width)
            min_height = min(700, max_height)

            # Center the window on screen
            x = (screen_width - max_width) // 2
            y = (screen_height - max_height) // 2

            self.setGeometry(x, y, max_width, max_height)
            self.setMinimumSize(min_width, min_height)

            logger.info(f"Dynamic window sizing: {max_width}x{max_height} on {screen_width}x{screen_height} screen")

        except Exception as e:
            # Fallback to reasonable defaults if dynamic sizing fails
            logger.warning(f"Dynamic sizing failed, using defaults: {e}")
            self.setGeometry(100, 100, 1400, 900)
            self.setMinimumSize(1200, 700)

    def _create_pages(self):
        """Create all content pages"""
        # Dashboard - create based on UI mode
        if self.ui_mode == "redesigned":
            db_path = os.path.join(os.path.dirname(__file__), 'database', 'hkjc_races.db')
            self.dashboard = RedesignedHomePage(db_path=db_path)
            self.dashboard.view_race_details.connect(self._on_new_ui_race_details)
        else:
            self.dashboard = self._create_dashboard()
        self.content_stack.addWidget(self.dashboard)
        
        # Analytics
        self.analytics_tab = AnalysisTab()
        self.content_stack.addWidget(self.analytics_tab)
        
        # Database
        self.database_tab = DatabaseBrowser()
        self.content_stack.addWidget(self.database_tab)
        
        # Settings
        self.settings_tab = SettingsTab()
        self.content_stack.addWidget(self.settings_tab)

    def _create_dashboard(self):
        """Modern dashboard with cards"""
        dashboard = QWidget()
        layout = QVBoxLayout(dashboard)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Top row - Stats cards
        self.stats_container = QFrame()
        self.stats_layout = QHBoxLayout(self.stats_container)
        self.stats_layout.setSpacing(12)
        self.stats_layout.setContentsMargins(0, 0, 0, 0)
        
        self._refresh_stats_cards()
        
        layout.addWidget(self.stats_container)
        
        # Middle row - Race filter and grid
        races_header_layout = QHBoxLayout()
        
        self.dashboard_races_label = QLabel(self.tr("ACTIVE RACES"))
        self.dashboard_races_label.setStyleSheet("""
            font-size: 13px;
            font-weight: bold;
            color: #8b949e;
            text-transform: uppercase;
            letter-spacing: 1px;
        """)
        races_header_layout.addWidget(self.dashboard_races_label)
        races_header_layout.addStretch()

        
        layout.addLayout(races_header_layout)
        
        # Race grid container
        self.race_grid_container = QFrame()
        self.race_grid_container.setStyleSheet("background-color: transparent; border: none;")
        self.race_grid_layout = QGridLayout(self.race_grid_container)
        self.race_grid_layout.setSpacing(8)

        # Query real race data from database
        races = self._get_today_races("all")

        for i, (race_date, race_num, race_name, time, venue) in enumerate(races):
            race_widget = self._create_race_card(race_date, race_num, race_name, time, venue)
            self.race_grid_layout.addWidget(race_widget, i // 2, i % 2)
        
        layout.addWidget(self.race_grid_container)
        
        layout.addStretch()
        
        return dashboard

    def _refresh_stats_cards(self):
        """Refresh statistics cards with current language"""
        # Clear existing
        while self.stats_layout.count():
            item = self.stats_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        stats_data = self._calculate_real_stats()
        for title_key, value, color, change in stats_data:
            # title_key is already the display string in this implementation, 
            # but we pass it through tr() to handle translation
            card = self._create_stat_card(self.tr(title_key), value, color, change)
            self.stats_layout.addWidget(card)

    def _create_stat_card(self, title, value, color, change):
        """Create a statistics card"""
        card = QFrame()
        card.setFixedHeight(120)
        card.setObjectName("statCard")  # ← THIS IS CRITICAL!
        
        card.setStyleSheet("""
            QFrame#statCard {
                background-color: #161b22;
                border: 6px solid #30363d;
                border-radius: 8px;
            }
        """)
            
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 11px;
            color: #8b949e;
            text-transform: uppercase;
            letter-spacing: 1px;
        """)
        layout.addWidget(title_label)
        
        # Value
        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            font-size: 28px;
            font-weight: bold;
            color: {color};
        """)
        layout.addWidget(value_label)
        
        # Change
        change_label = QLabel(change)
        change_label.setStyleSheet("""
            font-size: 11px;
            color: #8b949e;
        """)
        layout.addWidget(change_label)
        
        layout.addStretch()
        
        return card
    
    def _create_race_card(self, race_date: str, race_num: int, race: str, time: str, venue: str):
        """Create a clickable race card widget"""
        card = ClickableRaceCard(race_date, race_num, race, time, venue)
        card.race_clicked.connect(self._on_dashboard_race_clicked)
        return card
    
    def _on_dashboard_race_clicked(self, race_date: str, race_num: int):
        """Handle click on dashboard race card"""
        modal = RacePredictionModal(race_date, race_num, self)
        modal.exec_()
    
    def _on_race_card_selected(self, race_date: str, race_num: int):
        """Handle click on race card from race cards page"""
        modal = RacePredictionModal(race_date, race_num, self)
        modal.exec_()

    def _calculate_real_stats(self):
        """Calculate real statistics from database"""
        try:
            import sqlite3
            from datetime import datetime

            db_path = os.path.join(os.path.dirname(__file__), 'database', 'hkjc_races.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Use today's date for future races only
            today_date = datetime.now().strftime('%Y-%m-%d')

            stats_data = []

            # 1. Today's Races - count from fixtures table (actual future race schedule)
            cursor.execute('''
                SELECT COUNT(*) FROM fixtures
                WHERE DATE(race_date) = ?
            ''', (today_date,))
            today_races = cursor.fetchone()[0]

            stats_data.append(("今日賽事", str(today_races), "#238636", "0"))

            # 2. Races Analyzed - total races with results in database
            cursor.execute('SELECT COUNT(DISTINCT race_date || "-" || race_number) FROM race_results')
            total_analyzed = cursor.fetchone()[0]

            stats_data.append(("已分析賽事", f"{total_analyzed:,}", "#58a6ff", "歷史數據"))

            # 3. Total Horses - count from horses table
            cursor.execute('SELECT COUNT(*) FROM horses')
            total_horses = cursor.fetchone()[0]

            stats_data.append(("總馬匹數", f"{total_horses:,}", "#f0883e", "數據庫中"))

            conn.close()
            return stats_data

        except Exception as e:
            logger.error(f"Error calculating real stats: {e}")
            return []

    def _get_today_races(self, filter_type="all"):
        """Get today's races from database with optional filtering
        
        Args:
            filter_type: "all" (default), "with_results", or "without_results"
        """
        try:
            import sqlite3
            from datetime import datetime

            # Connect to database
            db_path = os.path.join(os.path.dirname(__file__), 'database', 'hkjc_races.db')
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get today's date
            today = datetime.now().strftime('%Y-%m-%d')

            if filter_type == "with_results":
                cursor.execute('''
                    SELECT DISTINCT f.race_date, f.race_number, f.racecourse, f.race_distance, f.race_class, f.track_going
                    FROM future_race_cards f
                    INNER JOIN race_results r ON DATE(f.race_date) = r.race_date AND f.race_number = r.race_number
                    ORDER BY DATE(f.race_date) DESC, f.race_number
                    LIMIT 11
                ''')
            elif filter_type == "without_results":
                cursor.execute('''
                    SELECT DISTINCT f.race_date, f.race_number, f.racecourse, f.race_distance, f.race_class, f.track_going
                    FROM future_race_cards f
                    WHERE NOT EXISTS (
                        SELECT 1 FROM race_results r 
                        WHERE DATE(f.race_date) = r.race_date AND f.race_number = r.race_number
                    )
                    ORDER BY DATE(f.race_date), f.race_number
                    LIMIT 11
                ''')
            else:
                cursor.execute('''
                    SELECT DISTINCT race_date, race_number, racecourse, race_distance, race_class, track_going
                    FROM future_race_cards
                    ORDER BY race_date, race_number
                    LIMIT 11
                ''')

            races = cursor.fetchall()
            conn.close()

            # Format the data for display
            formatted_races = []

            for race in races:
                race_date, race_num, venue, distance, race_class, going = race
                
                normalized_date = race_date
                if ' ' in str(race_date):
                    normalized_date = str(race_date).split(' ')[0]
                
                race_name = f"Race {race_num}"
                try:
                    race_datetime = datetime.strptime(normalized_date, '%Y-%m-%d')
                    today = datetime.now()
                    if race_datetime.date() == today.date():
                        formatted_date = "Today"
                    elif race_datetime.date() == (today + timedelta(days=1)).date():
                        formatted_date = "Tomorrow"
                    else:
                        formatted_date = race_datetime.strftime('%b %d')
                except:
                    formatted_date = normalized_date

                time = formatted_date 
                formatted_races.append((normalized_date, race_num, race_name, time, venue))

            return formatted_races

        except Exception as e:
            import traceback
            logger.error(f"Error fetching today's races: {e}")
            logger.error(traceback.format_exc())
            return []
    
    def _on_race_filter_changed(self, filter_text):
        """Handle race filter change"""
        filter_map = {
            "All Races": "all",
            "With Results": "with_results",
            "Without Results": "without_results"
        }
        filter_type = filter_map.get(filter_text, "all")
        
        races = self._get_today_races(filter_type)
        
        while self.race_grid_layout.count():
            item = self.race_grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        for i, (race_date, race_num, race_name, time, venue) in enumerate(races):
            race_widget = self._create_race_card(race_date, race_num, race_name, time, venue)
            self.race_grid_layout.addWidget(race_widget, i // 2, i % 2)

    def _refresh_data(self):
        """Manually trigger data refresh for selected racecourse"""
        course = self.course_dropdown.currentText()
        self.status_label.setText(self.tr(f"REFRESHING {course}..."))
        
        # Start data loading worker
        self.worker = DataLoadingWorker(racecourse=course)
        self.worker.progress_update.connect(lambda msg, p: self.status_label.setText(f"{msg} ({p}%)"))
        self.worker.loading_complete.connect(self._on_refresh_complete)
        self.worker.loading_error.connect(lambda err: self.status_label.setText(f"ERROR: {err}"))
        self.worker.start()

    def _on_refresh_complete(self):
        """Handle completion of manual refresh"""
        self.status_label.setText(self.tr("LIVE"))
        self._populate_date_dropdown()
        if self.selected_date:
            self._update_all_components_with_date(self.selected_date)
        else:
            # If no date was selected before, try to select the first one
            if self.date_dropdown.count() > 0:
                self._apply_selected_date()

    def _switch_page(self, index):
        """Switch between pages"""
        if index < self.content_stack.count():
            self.content_stack.setCurrentIndex(index)
    
    def _toggle_ui_mode(self):
        """Toggle between original and redesigned UI"""
        if self.ui_mode == "original":
            self.ui_mode = "redesigned"
            self.ui_mode_btn.setText(self.tr("Old UI"))
            self.ui_mode_btn.setStyleSheet("""
                QPushButton {
                    background-color: #059669;
                    color: #f8fafc;
                    border: none;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #047857;
                }
            """)
            # Hide top bar elements in new UI (new UI has its own controls)
            self._set_top_bar_visible(False)
        else:
            self.ui_mode = "original"
            self.ui_mode_btn.setText(self.tr("New UI"))
            self.ui_mode_btn.setStyleSheet("""
                QPushButton {
                    background-color: #7c3aed;
                    color: #f8fafc;
                    border: none;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #6d28d9;
                }
            """)
            # Show top bar elements in old UI
            self._set_top_bar_visible(True)
        
        # Recreate dashboard with new mode
        self._recreate_dashboard()
        print(f"Switched to {self.ui_mode} UI mode")
    
    def _set_top_bar_visible(self, visible: bool):
        """Show/hide top bar elements (date dropdown, course dropdown, apply button)"""
        # Elements to hide/show when switching UI modes (title remains visible)
        widgets_to_toggle = [
            self.course_label,
            self.course_dropdown,
            self.date_label,
            self.date_dropdown,
            self.apply_btn
        ]
        for widget in widgets_to_toggle:
            if widget:
                widget.setVisible(visible)
    
    def _recreate_dashboard(self):
        """Recreate dashboard based on current UI mode"""
        # Find and remove old dashboard
        dashboard_index = self.content_stack.indexOf(self.dashboard)
        if dashboard_index >= 0:
            widget = self.content_stack.widget(dashboard_index)
            self.content_stack.removeWidget(widget)
            widget.deleteLater()
        
        # Create new dashboard
        if self.ui_mode == "redesigned":
            # Get database path
            db_path = os.path.join(os.path.dirname(__file__), 'database', 'hkjc_races.db')
            self.dashboard = RedesignedHomePage(db_path=db_path)
            self.dashboard.view_race_details.connect(self._on_new_ui_race_details)
        else:
            self.dashboard = self._create_dashboard()
        
        # Insert at index 0
        self.content_stack.insertWidget(0, self.dashboard)
        self.content_stack.setCurrentIndex(0)
    
    def _on_new_ui_race_details(self, race_date: str, race_number: int, racecourse: str):
        """Handle race details request from new UI"""
        # Show detailed prediction modal (now asynchronous)
        modal = PredictionDetailModal(race_date, race_number, racecourse, self)
        modal.exec_()

    def on_view_predictions(self, race_number: int):
        """Handle view predictions request"""
        # Switch to predictions page
        self.sidebar.setCurrentRow(1)
        self._switch_page(1)
        
        # Pass race number to predictions tab
        predictions_tab = self.content_stack.widget(1)
        if hasattr(predictions_tab, 'load_race'):
            predictions_tab.load_race(race_number)
    
    def _show_retraining_dialog(self):
        """Show retraining dialog"""
        dialog = RetrainingDialog(self)
        dialog.exec_()

    def _populate_date_dropdown(self):
        """Populate date dropdown with distinct dates from future_race_cards"""
        try:
            import sqlite3
            db_path = os.path.join(os.path.dirname(__file__), 'database', 'hkjc_races.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Get distinct dates from future_race_cards using DATE() function
            cursor.execute('SELECT DISTINCT DATE(race_date) FROM future_race_cards ORDER BY DATE(race_date)')
            dates = [row[0] for row in cursor.fetchall()]
            conn.close()

            if dates:
                self.date_dropdown.clear()
                self.date_dropdown.addItems(dates)
                # Set default to first available date
                if dates:
                    self.selected_date = dates[0]
            else:
                self.date_dropdown.addItem(self.tr("No dates available"))

        except Exception as e:
            print(f"Error populating date dropdown: {e}")
            self.date_dropdown.addItem(self.tr("Error loading dates"))

    def _apply_selected_date(self):
        """Apply the selected date from dropdown"""
        selected_date = self.date_dropdown.currentText()
        if selected_date and selected_date != self.tr("No dates available") and selected_date != self.tr("Error loading dates"):
            self.selected_date = selected_date
            print(f"Applied selected date: {selected_date}")

            # Update all components with the selected date
            self._update_all_components_with_date(selected_date)
        else:
            print("No valid date selected")

    def _update_all_components_with_date(self, selected_date: str):
        """Update all components with the selected date"""
        try:
            # Update dashboard race cards
            self._update_dashboard_races(selected_date)

            # Update database browser (race cards)
            if hasattr(self.database_tab, 'update_date_filter'):
                self.database_tab.update_date_filter(selected_date)

            # Update analysis tab if it has date-dependent content
            if hasattr(self.analytics_tab, 'update_selected_date'):
                self.analytics_tab.update_selected_date(selected_date)

            # Update settings tab prediction date
            if hasattr(self.settings_tab, 'update_selected_date'):
                self.settings_tab.update_selected_date(selected_date)

            print(f"Updated all components with date: {selected_date}")

        except Exception as e:
            print(f"Error updating components with date: {e}")

    def _update_dashboard_races(self, selected_date: str):
        """Update dashboard race cards for selected date"""
        try:
            # Clear existing race cards
            while self.race_grid_layout.count():
                item = self.race_grid_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            # Get races for selected date
            races = self._get_races_for_date(selected_date, "all")

            # Add new race cards
            for i, (race_date, race_num, race_name, time, venue) in enumerate(races):
                race_widget = self._create_race_card(race_date, race_num, race_name, time, venue)
                self.race_grid_layout.addWidget(race_widget, i // 2, i % 2)

        except Exception as e:
            print(f"Error updating dashboard races: {e}")

    def _get_races_for_date(self, selected_date: str, filter_type="all"):
        """Get races for a specific date"""
        try:
            import sqlite3
            from datetime import datetime

            db_path = os.path.join(os.path.dirname(__file__), 'database', 'hkjc_races.db')
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if filter_type == "with_results":
                cursor.execute('''
                    SELECT DATE(f.race_date) as race_date, f.race_number, f.racecourse, f.race_distance, f.race_class, f.track_going
                    FROM future_race_cards f
                    INNER JOIN race_results r ON DATE(f.race_date) = r.race_date AND f.race_number = r.race_number
                    WHERE DATE(f.race_date) = ?
                    GROUP BY DATE(f.race_date), f.race_number
                    ORDER BY f.race_number
                ''', (selected_date,))
            elif filter_type == "without_results":
                cursor.execute('''
                    SELECT DATE(f.race_date) as race_date, f.race_number, f.racecourse, f.race_distance, f.race_class, f.track_going
                    FROM future_race_cards f
                    WHERE DATE(f.race_date) = ? AND NOT EXISTS (
                        SELECT 1 FROM race_results r
                        WHERE DATE(f.race_date) = r.race_date AND f.race_number = r.race_number
                    )
                    GROUP BY DATE(f.race_date), f.race_number
                    ORDER BY f.race_number
                ''', (selected_date,))
            else:
                cursor.execute('''
                    SELECT DATE(race_date) as race_date, race_number, racecourse, race_distance, race_class, track_going
                    FROM future_race_cards
                    WHERE DATE(race_date) = ?
                    GROUP BY DATE(race_date), race_number
                    ORDER BY race_number
                ''', (selected_date,))

            races = cursor.fetchall()
            conn.close()

            # Format the data for display
            formatted_races = []
            for race in races:
                race_date, race_num, venue, distance, race_class, going = race

                normalized_date = selected_date
                race_name = f"Race {race_num}"
                formatted_date = self.tr("Selected Date")

                formatted_races.append((normalized_date, race_num, race_name, formatted_date, venue or self.tr("Unknown")))

            return formatted_races

        except Exception as e:
            print(f"Error fetching races for date {selected_date}: {e}")
            return []

    def change_language(self, language_name):
        """Switch application language"""
        success = True
        if language_name == "繁體中文":
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "i18n", "zh_HK.qm")
            if os.path.exists(path) and self.translator.load(path):
                QApplication.installTranslator(self.translator)
                logger.info("Language switched to Traditional Chinese")
                print("✓ Translation loaded successfully")
            else:
                logger.error(f"Failed to load translation file: {path}")
                print(f"✗ Failed to load translation from {path}")
                success = False
        else:
            QApplication.removeTranslator(self.translator)
            logger.info("Language switched to English")
            print("✓ Switched to English")
        
        if success:
            self.retranslate_ui()
        return success

    def retranslate_ui(self):
        """Update UI strings after language change"""
        self.setWindowTitle(self.tr("Mr. Chan Exclusive Edition"))
        
        # Update Top Bar
        if hasattr(self, 'title_label'):
            self.title_label.setText(self.tr("Mr. Chan Exclusive Edition"))
        if hasattr(self, 'course_label'):
            self.course_label.setText(self.tr("Course:"))
        if hasattr(self, 'date_label'):
            self.date_label.setText(self.tr("Date:"))
        if hasattr(self, 'apply_btn'):
            self.apply_btn.setText(self.tr("Apply"))
        if hasattr(self, 'refresh_btn'):
            self.refresh_btn.setToolTip(self.tr("Refresh Data"))
        if hasattr(self, 'retrain_btn'):
            self.retrain_btn.setToolTip(self.tr("Retrain Models"))
            
        # Update Sidebar
        if hasattr(self, 'nav_items_map'):
            for key, item in self.nav_items_map.items():
                item.setText(self.tr(key))
        if hasattr(self, 'metrics_label_item'):
            self.metrics_label_item.setText(self.tr("METRICS"))
            
        # Update Status Bar
        if hasattr(self, 'status_label'):
            self.status_label.setText(self.tr("LIVE"))
        if hasattr(self, 'db_status_label'):
            self.db_status_label.setText(self.tr("DB: CONNECTED"))

        # Update Dashboard
        if hasattr(self, 'dashboard_races_label'):
            self.dashboard_races_label.setText(self.tr("ACTIVE RACES"))
        if hasattr(self, 'stats_layout'):
            self._refresh_stats_cards()
            
        # Update Pages
        if hasattr(self, 'settings_tab'):
            self.settings_tab.retranslate_ui()
        if hasattr(self, 'analytics_tab'):
            self.analytics_tab.retranslate_ui()
        # Add other tabs here as they implement retranslate_ui

def check_dependencies():
    """Verify that all required dependencies are installed."""
    missing = []
    for module in ['requests', 'bs4', 'selenium', 'webdriver_manager', 'PyQt5', 'pandas', 'numpy']:
        try:
            if module == 'bs4':
                import bs4
            else:
                __import__(module)
        except ImportError:
            missing.append(module)
    
    if missing:
        print("\n" + "!"*60)
        print(f"CRITICAL ERROR: Missing dependencies: {', '.join(missing)}")
        print("Please install them using: pip install -r requirements.txt")
        print("!"*60 + "\n")
        return False
    return True

def main():
    """Main entry point"""
    # Check dependencies before starting
    check_dependencies()
    
    app = QApplication(sys.argv)
    
    # Show loading screen
    loading = LoadingScreen()
    loading.show()
    
    # Create main window (hidden)
    window = MainWindow()
    
    # Start data loading worker
    worker = DataLoadingWorker()
    worker.progress_update.connect(loading.set_loading_message)
    worker.loading_complete.connect(lambda: [
        loading.close(),
        window.show()
    ])
    worker.loading_error.connect(lambda err: [
        loading.show_error(err),
        loading.close(),
        window.show()
    ])
    worker.start()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    import os
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
