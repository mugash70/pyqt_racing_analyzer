#!/usr/bin/env python3
"""
Settings Tab – Manual scraping, predictions, and configuration
Modernized UI (single-file, drop-in replacement)
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame,
    QProgressBar, QTextEdit, QDateEdit, QSpinBox, QComboBox, QCheckBox,
    QGroupBox, QFormLayout, QDoubleSpinBox, QGridLayout
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QDate
from PyQt5.QtGui import QFont, QColor, QTextCursor
import os
from datetime import datetime


# ─────────────────────
# Global App Style
# ─────────────────────
APP_QSS = """
* {
    font-family: Arial;
    font-size: 10.5pt;
}

QWidget {
    background-color: #020617;
    color: #e5e7eb;
}

QLabel#PageTitle {
    font-size: 22px;
    font-weight: 700;
}

QLabel#SectionTitle {
    font-size: 15px;
    font-weight: 600;
}

QFrame.Card {
    background-color: #020617;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 16px;
}

QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {
    background-color: #020617;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 8px;
    min-height: 28px;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #e5e7eb;
    width: 0;
    height: 0;
}

QComboBox QAbstractItemView {
    background-color: #020617;
    border: 1px solid #334155;
    selection-background-color: #2563eb;
    color: #e5e7eb;
    padding: 4px;
}

QComboBox QAbstractItemView::item {
    padding: 50px 50px;
    border: none;
}

QComboBox QAbstractItemView::item:selected {
    background-color: #2563eb;
    color: white;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #1d4ed8;
}

QPushButton {
    background-color: #2563eb;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton:hover { background-color: #1d4ed8; }
QPushButton:disabled { background-color: #475569; }

QProgressBar {
    height: 22px;
    border-radius: 6px;
    background: #020617;
    border: 1px solid #334155;
}

QProgressBar::chunk {
    background-color: #22c55e;
    border-radius: 5px;
}

QTextEdit {
    background-color: #020617;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 10px;
    font-family: JetBrains Mono, Consolas, monospace;
    font-size: 9pt;
}
"""


# ─────────────────────
# Reusable Card
# ─────────────────────
class Card(QFrame):
    def __init__(self, title: str):
        super().__init__()
        self.setProperty("class", "Card")

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("SectionTitle")
        layout.addWidget(self.title_label)

        self.body = QVBoxLayout()
        self.body.setSpacing(10)
        layout.addLayout(self.body)

    def set_title(self, title: str):
        self.title_label.setText(title)


# ─────────────────────
# Workers (unchanged logic)
# ─────────────────────
class PredictionWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, race_date: str, racecourse: str):
        super().__init__()
        self.race_date = race_date
        self.racecourse = racecourse

    def run(self):
        try:
            self.progress.emit("Initializing prediction pipeline...")
            from backup.race_wise_prediction_pipeline import RaceWisePredictionPipeline

            pipeline = RaceWisePredictionPipeline()
            preds = pipeline.predict_future_races(self.race_date, self.racecourse)
            pipeline.export_predictions(preds, "predictions.csv")

            self.finished.emit({"status": "success", "count": len(preds)})
            pipeline.close()
        except Exception as e:
            self.error.emit(str(e))


class ScrapingWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, scrape_type, date_from, racecourse="ST", date_to=None):
        super().__init__()
        self.scrape_type = scrape_type
        self.date_from = date_from
        self.racecourse = racecourse
        self.date_to = date_to

    def run(self):
        try:
            import sys
            import os
            # Add parent directory to path for imports
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sys.path.insert(0, parent_dir)
            
            from scraper.pipeline import HKJCDataPipeline
            from datetime import datetime
            
            pipeline = HKJCDataPipeline()
            race_date = datetime.strptime(self.date_from, "%Y-%m-%d")
            
            # Create mapping from Chinese scraper names to English method calls
            scrape_type_map = {
                "賽事結果": "save_race_results",
                "未來賽事": "save_future_race_cards",
                "天氣數據": "save_weather",
                "練馬師王賠率": "update_trainer_king_odds",
                "賽日更改": "update_race_day_changes",
                "賽道選擇": "update_track_selection",
                "騎師統計": "save_jkc_stats",
                "練馬師統計": "save_tnc_stats",
                "从化轉移": "save_conghua_movement",
                "馬匹評分": "save_horse_ratings",
                "詳細晨操": "save_detailed_trackwork",
                "騎師最愛": "save_jockey_favourites",
                "練馬師最愛": "save_trainer_favourites",
                "標準時間": "save_standard_times",
                "騎師排名": "save_jockey_rankings",
                "練馬師排名": "save_trainer_rankings",
                "賽程表": "save_fixtures",
                "試閘資料": "save_barrier_tests",
                "賽事摘要": "save_last_race_summaries",
                "傷患記錄": "save_injury_records_v2",
                "風速追蹤": "save_wind_tracker",
                "對戰備忘": "save_battle_memorandum",
                "新馬介紹": "save_new_horse_introductions",
                "專業排班": "sync_professional_schedules",
                "同步排名": "sync_all_rankings"
            }
            
            method_name = scrape_type_map.get(self.scrape_type)
            
            if method_name:
                self.progress.emit(f"正在抓取{self.scrape_type}...")
                
                if method_name == "update_trainer_king_odds" or method_name == "update_race_day_changes" or method_name == "update_track_selection":
                    # Methods that take date string instead of datetime
                    records = getattr(pipeline, method_name)(self.date_from)
                elif method_name == "save_jkc_stats" or method_name == "save_tnc_stats" or method_name == "save_conghua_movement" or method_name == "save_horse_ratings" or method_name == "save_jockey_rankings" or method_name == "save_trainer_rankings" or method_name == "save_standard_times":
                    # Methods that take no parameters
                    records = getattr(pipeline, method_name)()
                elif method_name == "save_jockey_favourites" or method_name == "save_trainer_favourites":
                    # Methods with different parameter signatures
                    records = getattr(pipeline, method_name)()
                else:
                    # Standard methods with race_date and racecourse parameters
                    records = getattr(pipeline, method_name)(race_date, self.racecourse)
            else:
                records = 0
                
            self.progress.emit(f"完成: 保存了 {records} 條記錄")
            self.finished.emit({"status": "success", "records": records})
        except Exception as e:
            self.error.emit(str(e))


# ─────────────────────
# Settings Tab
# ─────────────────────
class SettingsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(APP_QSS)
        self.init_ui()

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(18)

        self.page_title = QLabel(self.tr("Settings & Data Management"))
        self.page_title.setObjectName("PageTitle")
        root.addWidget(self.page_title)

        # Language
        self.lang_card = Card(self.tr("Interface"))
        row = QHBoxLayout()
        self.lang_label = QLabel(self.tr("Language"))
        row.addWidget(self.lang_label)
        row.addStretch()
        self.lang_combo = QComboBox()
        self.lang_combo.setMinimumWidth(200)
        self.lang_combo.addItems(["English", "繁體中文"])
        # Set default to Chinese (index 1)
        self.lang_combo.setCurrentIndex(1)
        row.addWidget(self.lang_combo)
        
        self.lang_apply_btn = QPushButton(self.tr("Apply"))
        self.lang_apply_btn.clicked.connect(self.on_apply_language)
        row.addWidget(self.lang_apply_btn)
        
        self.lang_card.body.addLayout(row)
        root.addWidget(self.lang_card)

        # Scraper Grid with scroll area
        from PyQt5.QtWidgets import QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("border: none;")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scraper_card = Card(self.tr("Data Scrapers"))
        
        # Date selector for scrapers
        date_row = QHBoxLayout()
        date_row.addWidget(QLabel(self.tr("賽道:")))
        self.scraper_course = QComboBox()
        self.scraper_course.addItems(["沙田", "跑馬地"])
        self.scraper_course.setMinimumWidth(80)
        date_row.addWidget(self.scraper_course)
        
        date_row.addSpacing(20)
        
        date_row.addWidget(QLabel(self.tr("日期:")))
        self.scraper_date = QDateEdit(QDate.currentDate())
        self.scraper_date.setMinimumWidth(150)
        self.scraper_date.setCalendarPopup(True)
        self.scraper_date.setDisplayFormat("yyyy-MM-dd")
        date_row.addWidget(self.scraper_date)
        date_row.addStretch()
        self.scraper_card.body.addLayout(date_row)
        
        # Grid of scraper buttons
        grid = QGridLayout()
        grid.setSpacing(20)
        scrapers = [
            ("賽事結果", "#2563eb"),
            ("未來賽事", "#2563eb"),
            ("天氣數據", "#2563eb"),
            ("練馬師王賠率", "#2563eb"),
            ("賽日更改", "#2563eb"),
            ("賽道選擇", "#2563eb"),
            ("騎師統計", "#2563eb"),
            ("練馬師統計", "#2563eb"),
            ("从化轉移", "#2563eb"),
            ("馬匹評分", "#2563eb"),
            ("詳細晨操", "#2563eb"),
            ("騎師最愛", "#2563eb"),
            ("練馬師最愛", "#2563eb"),
            ("標準時間", "#2563eb"),
            ("騎師排名", "#2563eb"),
            ("練馬師排名", "#2563eb"),
            ("賽程表", "#0891b2"),
            ("試閘資料", "#0891b2"),
            ("賽事摘要", "#0891b2"),
            ("傷患記錄", "#0891b2"),
            ("風速追蹤", "#0891b2"),
            ("對戰備忘", "#0891b2"),
            ("新馬介紹", "#0891b2"),
            ("專業排班", "#7c3aed"),
            ("同步排名", "#7c3aed")
        ]
        
        self.scraper_buttons = {}
        self.scraper_progress = {}
        self.scraper_button_order = []  # Track button creation order
        
        for i, (name, color) in enumerate(scrapers):
            # Create container for button and progress
            container = QFrame()
            container.setStyleSheet("""
                QFrame {
                    background-color: #1e293b;
                    border-radius: 8px;
                    padding: 8px;
                }
            """)
            container_layout = QVBoxLayout(container)
            container_layout.setSpacing(6)
            container_layout.setContentsMargins(8, 8, 8, 8)
            btn = QPushButton(name)
            btn.setMinimumHeight(40)
            btn.setMinimumWidth(140)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    border: none;
                    border-radius: 6px;
                    color: white;
                    font-weight: 600;
                    font-size: 11px;
                    padding: 8px;
                    text-align: center;
                }}
                QPushButton:hover {{
                    background-color: #1d4ed8;
                }}
                QPushButton:disabled {{
                    background-color: #475569;
                }}
            """)
            
            progress = QProgressBar()
            progress.setVisible(False)
            progress.setMaximum(0)
            progress.setFixedHeight(6)
            progress.setStyleSheet("""
                QProgressBar {
                    border: none;
                    background-color: #334155;
                    border-radius: 3px;
                    height: 6px;
                }
                QProgressBar::chunk {
                    background-color: #22c55e;
                    border-radius: 3px;
                }
            """)
            
            container_layout.addWidget(btn)
            container_layout.addWidget(progress)
            
            grid.addWidget(container, i // 4, i % 4)
            
            self.scraper_buttons[name] = btn
            self.scraper_progress[name] = progress
            self.scraper_button_order.append(name)  # Track order
            
            # Connect button to handler
            btn.clicked.connect(lambda checked, n=name: self.start_individual_scraper(n))
        
        self.scraper_card.body.addLayout(grid)
        scroll_layout.addWidget(self.scraper_card)
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_content)
        root.addWidget(scroll_area)

        # Scraper log
        self.scraper_log = QTextEdit()
        self.scraper_log.setMaximumHeight(120)
        root.addWidget(self.scraper_log)

        root.addStretch()
        
        # Initial translation setup
        self.retranslate_ui()

    def retranslate_ui(self):
        """Update UI strings after language change"""
        # English and Chinese translations
        if self.lang_combo.currentText() == "English":
            self.page_title.setText(self.tr("Settings & Data Management"))
            self.lang_card.set_title(self.tr("Interface"))
            self.lang_label.setText(self.tr("Language"))
            self.lang_apply_btn.setText(self.tr("Apply"))
            self.scraper_card.set_title(self.tr("Data Scrapers"))
            
            # Update scraper button texts to English
            scrapers = [
                ("Race Results", "#2563eb"),
                ("Future Race Cards", "#2563eb"),
                ("Weather", "#2563eb"),
                ("Trainer King Odds", "#2563eb"),
                ("Race Day Changes", "#2563eb"),
                ("Track Selection", "#2563eb"),
                ("Jockey Stats", "#2563eb"),
                ("Trainer Stats", "#2563eb"),
                ("Conghua Movement", "#2563eb"),
                ("Horse Ratings", "#2563eb"),
                ("Detailed Trackwork", "#2563eb"),
                ("Jockey Favourites", "#2563eb"),
                ("Trainer Favourites", "#2563eb"),
                ("Standard Times", "#2563eb"),
                ("Jockey Rankings", "#2563eb"),
                ("Trainer Rankings", "#2563eb"),
                ("Fixtures", "#0891b2"),
                ("Barrier Tests", "#0891b2"),
                ("Race Summaries", "#0891b2"),
                ("Injury Records", "#0891b2"),
                ("Wind Tracker", "#0891b2"),
                ("Battle Memo", "#0891b2"),
                ("New Horses", "#0891b2"),
                ("Pro Schedules", "#7c3aed"),
                ("Sync Rankings", "#7c3aed")
            ]
        else:
            # Default to Traditional Chinese
            self.page_title.setText("設置與數據管理")
            self.lang_card.set_title("界面")
            self.lang_label.setText("語言")
            self.lang_apply_btn.setText("應用")
            self.scraper_card.set_title("數據抓取")
            
            # Update scraper button texts to Traditional Chinese
            scrapers = [
                ("賽事結果", "#2563eb"),
                ("未來賽事", "#2563eb"),
                ("天氣數據", "#2563eb"),
                ("練馬師王賠率", "#2563eb"),
                ("賽日更改", "#2563eb"),
                ("賽道選擇", "#2563eb"),
                ("騎師統計", "#2563eb"),
                ("練馬師統計", "#2563eb"),
                ("从化轉移", "#2563eb"),
                ("馬匹評分", "#2563eb"),
                ("詳細晨操", "#2563eb"),
                ("騎師最愛", "#2563eb"),
                ("練馬師最愛", "#2563eb"),
                ("標準時間", "#2563eb"),
                ("騎師排名", "#2563eb"),
                ("練馬師排名", "#2563eb"),
                ("賽程表", "#0891b2"),
                ("試閘資料", "#0891b2"),
                ("賽事摘要", "#0891b2"),
                ("傷患記錄", "#0891b2"),
                ("風速追蹤", "#0891b2"),
                ("對戰備忘", "#0891b2"),
                ("新馬介紹", "#0891b2"),
                ("專業排班", "#7c3aed"),
                ("同步排名", "#7c3aed")
            ]

        # Update racecourse dropdown options
        self.scraper_course.clear()
        if self.lang_combo.currentText() == "English":
            self.scraper_course.addItems(["Sha Tin", "Happy Valley"])
        else:
            self.scraper_course.addItems(["沙田", "跑馬地"])
            
        # Update date selector labels
        for i in range(self.scraper_card.body.count()):
            item = self.scraper_card.body.itemAt(i)
            if item and isinstance(item, QHBoxLayout):
                layout = item
                for j in range(layout.count()):
                    widget = layout.itemAt(j).widget()
                    if widget and isinstance(widget, QLabel):
                        if self.lang_combo.currentText() == "English":
                            if widget.text() == "賽道:":
                                widget.setText("Course:")
                            elif widget.text() == "日期:":
                                widget.setText("Date:")
                        else:
                            if widget.text() == "Course:":
                                widget.setText("賽道:")
                            elif widget.text() == "Date:":
                                widget.setText("日期:")

        # Update each scraper button text by index (using tracked order)
        for i, (name, color) in enumerate(scrapers):
            if i < len(self.scraper_button_order):
                button_name = self.scraper_button_order[i]
                if button_name in self.scraper_buttons:
                    self.scraper_buttons[button_name].setText(name)

    # ───────── Handlers ─────────
    def on_apply_language(self):
        language = self.lang_combo.currentText()
        main_window = self.window()
        if hasattr(main_window, 'change_language'):
            success = main_window.change_language(language)
            if success:
                # Update UI with new language
                self.retranslate_ui()
            else:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, self.tr("Error"), 
                                  self.tr("Failed to load translation file. Ensure that .qm file exists."))

    def start_individual_scraper(self, scraper_name):
        """Start individual scraper with progress tracking"""
        self.scraper_log.append(f"Starting {scraper_name}...")
        
        # Show progress bar and change button to cancel
        self.scraper_progress[scraper_name].setVisible(True)
        self.scraper_buttons[scraper_name].setText(self.tr("Cancel"))
        self.scraper_buttons[scraper_name].setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                border: none;
                border-radius: 6px;
                color: white;
                font-weight: 600;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
        """)
        self.scraper_buttons[scraper_name].clicked.disconnect()
        self.scraper_buttons[scraper_name].clicked.connect(lambda: self.cancel_scraper(scraper_name))
        
        # Translate Chinese racecourse names to pipeline format
        course_map = {"沙田": "ST", "跑馬地": "HV"}
        racecourse = course_map.get(self.scraper_course.currentText(), "ST")
        
        # Start worker
        self.current_worker = ScrapingWorker(
            scraper_name,
            self.scraper_date.date().toString("yyyy-MM-dd"),
            racecourse
        )
        self.current_worker.progress.connect(self.scraper_log.append)
        self.current_worker.finished.connect(lambda result: self.on_scraper_finished(scraper_name, result))
        self.current_worker.error.connect(lambda err: self.on_scraper_error(scraper_name, err))
        self.current_worker.start()
    
    def cancel_scraper(self, scraper_name):
        """Cancel running scraper"""
        if hasattr(self, 'current_worker') and self.current_worker.isRunning():
            self.current_worker.terminate()
            self.current_worker.wait()
        self.scraper_log.append(f"✗ {scraper_name} cancelled")
        self.reset_scraper_button(scraper_name)
    
    def reset_scraper_button(self, scraper_name):
        """Reset button to original state"""
        self.scraper_progress[scraper_name].setVisible(False)
        self.scraper_buttons[scraper_name].setText(scraper_name)
        
        # Get original color (consistent blue)
        color = "#2563eb"
        
        self.scraper_buttons[scraper_name].setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border: none;
                border-radius: 6px;
                color: white;
                font-weight: 600;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: #1d4ed8;
            }}
        """)
        self.scraper_buttons[scraper_name].clicked.disconnect()
        self.scraper_buttons[scraper_name].clicked.connect(lambda: self.start_individual_scraper(scraper_name))
    
    def on_scraper_finished(self, scraper_name, result):
        """Handle scraper completion"""
        records = result.get('records', 0)
        self.scraper_log.append(f"✓ {scraper_name} completed: {records} records")
        self.reset_scraper_button(scraper_name)
        
        # Notify main window to refresh date dropdown if new data was scraped
        if records > 0:
            main_window = self.window()
            if hasattr(main_window, '_populate_date_dropdown'):
                main_window._populate_date_dropdown()
    
    def on_scraper_error(self, scraper_name, error):
        """Handle scraper error"""
        self.scraper_log.append(f"✗ {scraper_name} failed: {error}")
        self.reset_scraper_button(scraper_name)

    def start_prediction(self):
        self.pred_log.clear()
        self.pred_progress.setVisible(True)
        self.worker = PredictionWorker("2026-01-11", "ST")
        self.worker.progress.connect(self.pred_log.append)
        self.worker.finished.connect(lambda _: self.pred_progress.setVisible(False))
        self.worker.error.connect(self.pred_log.append)
        self.worker.start()

