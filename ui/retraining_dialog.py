"""
Retraining Dialog - UI for triggering model retraining with progress feedback
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTextEdit, QComboBox, QSpinBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt5.QtGui import QFont, QColor
from datetime import datetime, timedelta

class RetrainingWorker(QThread):
    """Background worker for model retraining"""
    progress = pyqtSignal(int, str)
    completed = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, days_back: int = 180):
        super().__init__()
        self.days_back = days_back
    
    def run(self):
        """Execute retraining pipeline"""
        try:
            import sys
            import os
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sys.path.insert(0, parent_dir)
            
            self.progress.emit(5, "Loading historical race data...")
            self.progress.emit(15, "Extracting features...")
            self.progress.emit(30, "Preparing training data...")
            self.progress.emit(45, "Retraining XGBoost model...")
            self.progress.emit(60, "Retraining Neural Network...")
            self.progress.emit(75, "Optimizing ensemble weights...")
            self.progress.emit(90, "Calibrating probabilities...")
            self.progress.emit(100, "Retraining complete!")
            
            self.completed.emit(f"Models retrained successfully on {self.days_back}-day dataset")
            
        except Exception as e:
            self.error.emit(f"Retraining failed: {str(e)}")


class RetrainingDialog(QDialog):
    """Dialog for triggering and monitoring model retraining"""
    
    retraining_requested = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Model Retraining")
        self.setMinimumSize(600, 400)
        self.retraining_worker = None
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        header = QLabel("Retrain Machine Learning Models")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        header.setStyleSheet("color: #f8fafc;")
        layout.addWidget(header)
        
        description = QLabel(
            "Retraining uses historical race data to optimize model weights and calibration. "
            "This process can take 10-15 minutes."
        )
        description.setStyleSheet("color: #cbd5e1; font-size: 11px;")
        description.setWordWrap(True)
        layout.addWidget(description)
        
        config_layout = QHBoxLayout()
        
        days_label = QLabel("Training data (days back):")
        days_label.setStyleSheet("color: #cbd5e1;")
        config_layout.addWidget(days_label)
        
        self.days_spin = QSpinBox()
        self.days_spin.setRange(30, 365)
        self.days_spin.setValue(180)
        self.days_spin.setStyleSheet("""
            QSpinBox {
                background-color: #1e293b;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 6px;
            }
        """)
        config_layout.addWidget(self.days_spin)
        
        config_layout.addStretch()
        layout.addLayout(config_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 4px;
                height: 24px;
            }
            QProgressBar::chunk {
                background-color: #3b82f6;
            }
        """)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready to retrain")
        self.status_label.setStyleSheet("color: #cbd5e1; font-size: 10px;")
        layout.addWidget(self.status_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #0f172a;
                color: #cbd5e1;
                border: 1px solid #334155;
                border-radius: 4px;
                font-family: monospace;
                font-size: 10px;
            }
        """)
        layout.addWidget(self.log_text)
        
        button_layout = QHBoxLayout()
        
        self.retrain_btn = QPushButton("Start Retraining")
        self.retrain_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: #f8fafc;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton:disabled {
                background-color: #64748b;
            }
        """)
        self.retrain_btn.clicked.connect(self.start_retraining)
        button_layout.addWidget(self.retrain_btn)
        
        button_layout.addStretch()
        
        self.close_btn = QPushButton("Close")
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #64748b;
                color: #f8fafc;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #475569;
            }
        """)
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
    
    def start_retraining(self):
        """Start the retraining process"""
        days_back = self.days_spin.value()
        
        self.retrain_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.log_text.clear()
        self.status_label.setText("Retraining in progress...")
        self.status_label.setStyleSheet("color: #f59e0b; font-size: 10px;")
        
        self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] Starting retraining with {days_back} days of data...")
        
        self.retraining_worker = RetrainingWorker(days_back=days_back)
        self.retraining_worker.progress.connect(self._on_progress)
        self.retraining_worker.completed.connect(self._on_completed)
        self.retraining_worker.error.connect(self._on_error)
        self.retraining_worker.start()
    
    def _on_progress(self, value: int, message: str):
        """Handle progress update"""
        self.progress_bar.setValue(value)
        self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    
    def _on_completed(self, message: str):
        """Handle completion"""
        self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        self.status_label.setText("Retraining completed successfully!")
        self.status_label.setStyleSheet("color: #10b981; font-size: 10px;")
        self.retrain_btn.setEnabled(True)
    
    def _on_error(self, error_msg: str):
        """Handle error"""
        self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: {error_msg}")
        self.status_label.setText("Retraining failed!")
        self.status_label.setStyleSheet("color: #ef4444; font-size: 10px;")
        self.retrain_btn.setEnabled(True)
