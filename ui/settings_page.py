"""
Settings Page - Data Refresh and Model Training Controls
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTextEdit, QProgressBar, QGroupBox, QGridLayout, QFrame, QMessageBox,
    QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QIntValidator

from .styles import COLORS


class SettingsPage(QWidget):
    """Settings page for data management and model training"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.data_refresh_worker = None
        self.training_worker = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the settings UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("Data & Model Settings")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #f8fafc; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Create main content area with two columns
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # Left column - Data Refresh
        left_panel = self.create_data_refresh_panel()
        content_layout.addWidget(left_panel, 1)
        
        # Right column - Training and Stats
        right_panel = self.create_training_stats_panel()
        content_layout.addWidget(right_panel, 1)
        
        layout.addLayout(content_layout)
        
        # Log output at bottom
        log_group = self.create_log_panel()
        layout.addWidget(log_group)
        
        # Spacer at bottom
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
    def create_data_refresh_panel(self) -> QGroupBox:
        """Create the data refresh control panel"""
        group = QGroupBox("Data Refresh / Scraping")
        group.setStyleSheet("""
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
        
        layout = QVBoxLayout(group)
        layout.setContentsMargins(15, 25, 15, 15)
        layout.setSpacing(15)
        
        # Description
        desc = QLabel("Scrape new race data from HKJC website and append to existing database.")
        desc.setStyleSheet("color: #cbd5e1; font-size: 12px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Days input
        days_layout = QHBoxLayout()
        days_label = QLabel("Lookback Days:")
        days_label.setStyleSheet("color: #f8fafc; font-size: 13px;")
        days_layout.addWidget(days_label)
        
        self.scrape_days_input = QLineEdit("7")
        self.scrape_days_input.setStyleSheet("""
            QLineEdit {
                background-color: #0f172a;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 6px;
                font-size: 13px;
                width: 60px;
            }
        """)
        self.scrape_days_input.setValidator(QIntValidator(1, 365))
        self.scrape_days_input.setMaximumWidth(80)
        days_layout.addWidget(self.scrape_days_input)
        days_layout.addStretch()
        layout.addLayout(days_layout)
        
        # Progress bar
        self.scrape_progress = QProgressBar()
        self.scrape_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #334155;
                border-radius: 4px;
                background-color: #0f172a;
                text-align: center;
                color: #f8fafc;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #3b82f6;
                border-radius: 3px;
            }
        """)
        self.scrape_progress.setValue(0)
        self.scrape_progress.setVisible(False)
        layout.addWidget(self.scrape_progress)
        
        # Stage indicator
        self.scrape_stage = QLabel("")
        self.scrape_stage.setStyleSheet("color: #3b82f6; font-size: 12px; font-style: italic;")
        layout.addWidget(self.scrape_stage)
        
        # Start button
        self.scrape_button = QPushButton("Start Data Scraping")
        self.scrape_button.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: #f8fafc;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: 500;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:disabled {
                background-color: #64748b;
            }
        """)
        self.scrape_button.clicked.connect(self.start_data_refresh)
        layout.addWidget(self.scrape_button)
        
        # Race count display
        self.races_scraped_label = QLabel("Races scraped: 0")
        self.races_scraped_label.setStyleSheet("color: #cbd5e1; font-size: 12px;")
        layout.addWidget(self.races_scraped_label)
        
        layout.addStretch()
        return group
        
    def create_training_stats_panel(self) -> QWidget:
        """Create the training panel and data stats"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(20)
        
        # Training section
        training_group = QGroupBox("Model Training")
        training_group.setStyleSheet("""
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
        
        train_layout = QVBoxLayout(training_group)
        train_layout.setContentsMargins(15, 25, 15, 15)
        train_layout.setSpacing(15)
        
        # Description
        desc = QLabel("Train the ML ensemble model on recent race data. Default: 30 days.")
        desc.setStyleSheet("color: #cbd5e1; font-size: 12px;")
        desc.setWordWrap(True)
        train_layout.addWidget(desc)
        
        # Days input
        days_layout = QHBoxLayout()
        days_label = QLabel("Training Days:")
        days_label.setStyleSheet("color: #f8fafc; font-size: 13px;")
        days_layout.addWidget(days_label)
        
        self.training_days_input = QLineEdit("30")
        self.training_days_input.setStyleSheet("""
            QLineEdit {
                background-color: #0f172a;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 6px;
                font-size: 13px;
                width: 60px;
            }
        """)
        self.training_days_input.setValidator(QIntValidator(1, 365))
        self.training_days_input.setMaximumWidth(80)
        days_layout.addWidget(self.training_days_input)
        days_layout.addStretch()
        train_layout.addLayout(days_layout)
        
        # Training progress bar
        self.training_progress = QProgressBar()
        self.training_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #334155;
                border-radius: 4px;
                background-color: #0f172a;
                text-align: center;
                color: #f8fafc;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #f59e0b;
                border-radius: 3px;
            }
        """)
        self.training_progress.setValue(0)
        self.training_progress.setVisible(False)
        train_layout.addWidget(self.training_progress)
        
        # Training stage indicator
        self.training_stage = QLabel("")
        self.training_stage.setStyleSheet("color: #f59e0b; font-size: 12px; font-style: italic;")
        train_layout.addWidget(self.training_stage)
        
        # Start training button
        self.train_button = QPushButton("Start Model Training")
        self.train_button.setStyleSheet("""
            QPushButton {
                background-color: #f59e0b;
                color: #f8fafc;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: 500;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #d97706;
            }
            QPushButton:disabled {
                background-color: #64748b;
            }
        """)
        self.train_button.clicked.connect(self.start_training)
        train_layout.addWidget(self.train_button)
        
        # Metrics display
        self.metrics_label = QLabel("")
        self.metrics_label.setStyleSheet("color: #cbd5e1; font-size: 11px;")
        self.metrics_label.setWordWrap(True)
        train_layout.addWidget(self.metrics_label)
        
        layout.addWidget(training_group)
        
        # Data Stats section
        stats_group = QGroupBox("Database Statistics")
        stats_group.setStyleSheet("""
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
        
        stats_layout = QGridLayout(stats_group)
        stats_layout.setContentsMargins(15, 25, 15, 15)
        stats_layout.setSpacing(12)
        
        # Stats items
        self.total_races_label = self.create_stat_item(stats_layout, "Total Races:", "0", 0)
        self.total_horses_label = self.create_stat_item(stats_layout, "Total Horses:", "0", 1)
        self.last_update_label = self.create_stat_item(stats_layout, "Last Updated:", "Never", 2)
        self.model_status_label = self.create_stat_item(stats_layout, "Model Status:", "Not loaded", 3)
        
        # Refresh stats button
        self.refresh_stats_button = QPushButton("Refresh Stats")
        self.refresh_stats_button.setStyleSheet("""
            QPushButton {
                background-color: #64748b;
                color: #f8fafc;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #334155;
            }
        """)
        self.refresh_stats_button.clicked.connect(self.refresh_stats)
        stats_layout.addWidget(self.refresh_stats_button, 4, 0, 1, 2)
        
        layout.addWidget(stats_group)
        
        # Initial stats load
        self.refresh_stats()
        return container
        
    def create_stat_item(self, layout: QGridLayout, label: str, default_value: str, row: int) -> QLabel:
        """Create a statistics item row"""
        name_label = QLabel(label)
        name_label.setStyleSheet("color: #cbd5e1; font-size: 12px;")
        layout.addWidget(name_label, row, 0)
        
        value_label = QLabel(default_value)
        value_label.setStyleSheet("color: #f8fafc; font-size: 12px; font-weight: 500;")
        layout.addWidget(value_label, row, 1)
        return value_label
        
    def create_log_panel(self) -> QGroupBox:
        """Create the log output panel"""
        group = QGroupBox("Pipeline Progress Log")
        group.setStyleSheet("""
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
        
        layout = QVBoxLayout(group)
        layout.setContentsMargins(15, 25, 15, 15)
        
        # Log text area
        self.log_text = QTextEdit()
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
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        layout.addWidget(self.log_text)
        return group
        
    def log_message(self, message: str):
        """Add a message to the log window"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        scrollbar = self.log_text.verticalScrollBar()
        if scrollbar:
            scrollbar.setValue(scrollbar.maximum())
        
    def start_data_refresh(self):
        """Start the data refresh/scraping process"""
        try:
            days = int(self.scrape_days_input.text())
            if days < 1 or days > 365:
                QMessageBox.warning(self, "Invalid Input", "Please enter a valid number of days (1-365)")
                return
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid number")
            return
            
        self.scrape_button.setEnabled(False)
        self.scrape_progress.setVisible(True)
        self.scrape_progress.setValue(0)
        
        from ui.data_refresh_worker import DataRefreshWorker
        
        self.data_refresh_worker = DataRefreshWorker(lookback_days=days)
        self.data_refresh_worker.progress.connect(self.log_message)
        self.data_refresh_worker.stage_changed.connect(self.on_scrape_stage_changed)
        self.data_refresh_worker.races_scraped.connect(self.on_races_scraped)
        self.data_refresh_worker.finished.connect(self.on_scrape_finished)
        self.data_refresh_worker.error.connect(self.on_scrape_error)
        
        self.log_message(f"Starting data refresh for last {days} days...")
        self.data_refresh_worker.start()
        
    @pyqtSlot(str)
    def on_scrape_stage_changed(self, stage: str):
        """Handle scrape stage changes"""
        stage_names = {
            "initializing": "Initializing pipeline...",
            "fetching_dates": "Fetching available dates from HKJC...",
        }
        stage_text = stage_names.get(stage, stage)
        self.scrape_stage.setText(stage_text)
        
        if stage == "initializing":
            self.scrape_progress.setValue(10)
        elif stage == "fetching_dates":
            self.scrape_progress.setValue(25)
        elif stage == "completed":
            self.scrape_progress.setValue(100)
        else:
            self.scrape_progress.setValue(50)
            
    @pyqtSlot(int)
    def on_races_scraped(self, count: int):
        """Update race count"""
        self.races_scraped_label.setText(f"Races scraped: {count}")
        self.scrape_progress.setValue(75)
        
    @pyqtSlot(dict)
    def on_scrape_finished(self, results: dict):
        """Handle scrape completion"""
        self.scrape_button.setEnabled(True)
        self.scrape_stage.setText("Completed")
        self.scrape_progress.setValue(100)
        
        duration = results.get('duration_seconds', 0)
        races = results.get('races_scraped', 0)
        
        self.log_message(f"Data refresh complete: {races} races scraped in {duration:.1f} seconds")
        self.refresh_stats()
        
    @pyqtSlot(str)
    def on_scrape_error(self, error: str):
        """Handle scrape error"""
        self.scrape_button.setEnabled(True)
        self.scrape_stage.setText("Error occurred")
        self.log_message(f"ERROR: {error}")
        QMessageBox.critical(self, "Scraping Error", f"Failed to complete data refresh:\n{error}")
        
    def start_training(self):
        """Start the model training process"""
        try:
            days = int(self.training_days_input.text())
            if days < 1 or days > 365:
                QMessageBox.warning(self, "Invalid Input", "Please enter a valid number of days (1-365)")
                return
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid number")
            return
            
        self.train_button.setEnabled(False)
        self.training_progress.setVisible(True)
        self.training_progress.setValue(0)
        
        from ui.training_worker import TrainingWorker
        
        self.training_worker = TrainingWorker(days=days)
        self.training_worker.progress.connect(self.log_message)
        self.training_worker.stage_changed.connect(self.on_training_stage_changed)
        self.training_worker.stage_progress.connect(self.training_progress.setValue)
        self.training_worker.metrics_calculated.connect(self.on_metrics_calculated)
        self.training_worker.finished.connect(self.on_training_finished)
        self.training_worker.error.connect(self.on_training_error)
        
        self.log_message(f"Starting model training with {days} days of data...")
        self.training_worker.start()
        
    @pyqtSlot(str)
    def on_training_stage_changed(self, stage: str):
        """Handle training stage changes"""
        stage_names = {
            "initializing": "Initializing training...",
            "loading_data": "Loading training data...",
            "feature_engineering": "Engineering features...",
            "preprocessing": "Preprocessing data...",
            "training": "Training ensemble models...",
            "saving": "Saving trained models...",
        }
        stage_text = stage_names.get(stage, stage)
        self.training_stage.setText(stage_text)
        
    @pyqtSlot(dict)
    def on_metrics_calculated(self, metrics: dict):
        """Display training metrics"""
        acc = metrics.get('accuracy', 0)
        prec = metrics.get('precision', 0)
        rec = metrics.get('recall', 0)
        f1 = metrics.get('f1', 0)
        auc = metrics.get('roc_auc', 0)
        
        self.metrics_label.setText(f"Accuracy: {acc:.2%} | Precision: {prec:.2%} | Recall: {rec:.2%} | F1: {f1:.2%} | AUC: {auc:.2%}")
        
    @pyqtSlot(dict)
    def on_training_finished(self, results: dict):
        """Handle training completion"""
        self.train_button.setEnabled(True)
        self.training_stage.setText("Completed")
        self.training_progress.setValue(100)
        
        duration = results.get('training_time', 0)
        samples = results.get('samples_used', 0)
        
        self.log_message(f"Training complete in {duration:.1f} seconds using {samples} samples")
        
        # Update model status
        self.model_status_label.setText("Loaded")
        self.refresh_stats()
        
    @pyqtSlot(str)
    def on_training_error(self, error: str):
        """Handle training error"""
        self.train_button.setEnabled(True)
        self.training_stage.setText("Error occurred")
        self.log_message(f"ERROR: {error}")
        QMessageBox.critical(self, "Training Error", f"Failed to complete training:\n{error}")
        
    def refresh_stats(self):
        """Refresh database statistics"""
        import sqlite3
        import os
        
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'hkjc_races.db')
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Total races
            cursor.execute("SELECT COUNT(*) FROM races")
            total_races = cursor.fetchone()[0]
            
            # Total horses
            cursor.execute("SELECT COUNT(*) FROM horses")
            total_horses = cursor.fetchone()[0]
            
            # Last update (most recent scraped race)
            cursor.execute("SELECT MAX(scraped_at) FROM races")
            last_update = cursor.fetchone()[0]
            
            conn.close()
            
            self.total_races_label.setText(str(total_races))
            self.total_horses_label.setText(str(total_horses))
            self.last_update_label.setText(last_update if last_update else "Never")
            
        except Exception as e:
            self.log_message(f"Error loading stats: {e}")
       