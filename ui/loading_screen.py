

#!/usr/bin/env python3
"""
Loading Screen - Professional loading screen with large image
Displays progress during data pipeline initialization
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor
import math
import os

from .styles import COLORS


class LoadingScreen(QWidget):
    """Professional loading screen with large image"""

    loading_complete = pyqtSignal()
    loading_progress = pyqtSignal(str, int)  # message, percentage

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_step = 0
        self.total_steps = 5
        self.loading_steps = [
            "Initializing Data Pipeline...",
            "Loading Race Cards...",
            "Fetching Weather Data...",
            "Updating Horse Database...",
            "Processing Form Lines...",
            "Connecting Live Odds Feed..."
        ]
        
        # Your image path
        self.image_path = os.path.join(os.path.dirname(__file__), '..', 'loading.jpg')

        self.init_ui()
        self.start_loading_animation()

    def init_ui(self):
        """Initialize the loading screen UI - WITH LARGE IMAGE"""
        # Create main layout with centering
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 20, 30, 20)  # Adjusted margins
        
        # Add top spacer
        main_layout.addStretch(1)
        
        # ========== LARGE IMAGE SECTION ==========
        image_container = QWidget()
        image_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        image_layout = QVBoxLayout(image_container)
        image_layout.setContentsMargins(0, 0, 0, 20)  # Space below image
        
        # Load and display the image - LARGE SIZE
        self.image_label = QLabel()
        
        if os.path.exists(self.image_path):
            try:
                pixmap = QPixmap(self.image_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(380, 380, 
                                                 Qt.KeepAspectRatio, 
                                                 Qt.SmoothTransformation)
                    self.image_label.setPixmap(scaled_pixmap)
                    print(f"✓ Loaded image: {self.image_path}")
                else:
                    self.set_fallback_image("Image file corrupted")
            except Exception as e:
                print(f"Error loading image: {e}")
                self.set_fallback_image("Could not load image")
        else:
            print(f"Image not found: {self.image_path}")
            self.set_fallback_image("Image not found")
        
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: transparent;")
        image_layout.addWidget(self.image_label)
        
        main_layout.addWidget(image_container, alignment=Qt.AlignCenter)
        
        # ========== CONTENT SECTION ==========
        # Create centered container for loading content
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setSpacing(15)  # Tighter spacing
        
        # Title/Heading
        title_label = QLabel("Mr. Chan Exclusive Edition")
        title_label.setFont(QFont("Arial", 22, QFont.Bold))
        title_label.setStyleSheet(f"""
            color: {COLORS['accent_primary']};
            padding: 5px 0;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(title_label)
        
        # Current task
        self.task_label = QLabel("Initializing...")
        self.task_label.setFont(QFont("Arial", 14))
        self.task_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-weight: 500;
            padding: 5px 0;
        """)
        self.task_label.setAlignment(Qt.AlignCenter)
        self.task_label.setWordWrap(True)
        content_layout.addWidget(self.task_label)
        
        # Progress bar container
        progress_container = QWidget()
        progress_container.setFixedWidth(400)
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(5)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(16)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {COLORS['border_light']};
                border-radius: 8px;
                background-color: {COLORS['background_secondary']};
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['accent_primary']};
                border-radius: 8px;
            }}
        """)
        progress_layout.addWidget(self.progress_bar)
        
        # Percentage and status row
        status_row = QWidget()
        status_layout = QHBoxLayout(status_row)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(10)
        
        # Percentage label
        self.percentage_label = QLabel("0%")
        self.percentage_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.percentage_label.setStyleSheet(f"color: {COLORS['accent_primary']};")
        self.percentage_label.setAlignment(Qt.AlignCenter)
        
        # Status details
        self.status_label = QLabel("Preparing data connections...")
        self.status_label.setFont(QFont("Arial", 11))
        self.status_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        status_layout.addWidget(self.percentage_label)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        progress_layout.addWidget(status_row)
        content_layout.addWidget(progress_container, alignment=Qt.AlignCenter)
        
        # Set content widget layout
        content_widget.setLayout(content_layout)
        
        # Add content widget to main layout
        main_layout.addWidget(content_widget, alignment=Qt.AlignCenter)
        
        # Add bottom spacer
        main_layout.addStretch(1)
        
        # Footer
        footer = QLabel("Mr. Chan Exclusive Edition")
        footer.setFont(QFont("Arial", 10))
        footer.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            padding-top: 20px;
            font-style: italic;
        """)
        footer.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(footer)
        
        self.setLayout(main_layout)
        self.setStyleSheet(f"background-color: {COLORS['background_primary']};")
        
        # Set size policy to allow proper centering
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_fallback_image(self, reason: str = ""):
        """Set fallback if image fails to load"""
        print(f"Using fallback image: {reason}")
        self.image_label.setText("🏇")
        self.image_label.setFont(QFont("Arial", 100))  # Large emoji
        self.image_label.setStyleSheet(f"""
            background-color: transparent;
            color: {COLORS['accent_primary']};
        """)

    def start_loading_animation(self):
        """Start the loading animation sequence"""
        pass  # Real progress updates come from DataLoadingWorker

    def set_loading_message(self, message: str, progress: int):
        """Update loading message and progress externally"""
        self.task_label.setText(message)
        self.progress_bar.setValue(progress)
        self.status_label.setText(f"Progress: {progress}%")
        self.percentage_label.setText(f"{progress}%")
        
        # Smooth animation for progress bar
        animation = QPropertyAnimation(self.progress_bar, b"value")
        animation.setDuration(300)
        animation.setStartValue(self.progress_bar.value() - 10 if self.progress_bar.value() > 10 else 0)
        animation.setEndValue(progress)
        animation.setEasingCurve(QEasingCurve.OutQuad)
        animation.start()
        
        # Special styling for 100%
        if progress == 100:
            self.task_label.setText("Ready!")
            self.task_label.setStyleSheet(f"""
                color: {COLORS['accent_success']};
                font-weight: bold;
                font-size: 16px;
            """)
            self.status_label.setText("All systems initialized successfully")
            
            # Change progress bar to success color
            self.progress_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: 1px solid {COLORS['accent_success']};
                    border-radius: 8px;
                    background-color: {COLORS['background_secondary']};
                }}
                QProgressBar::chunk {{
                    background-color: {COLORS['accent_success']};
                    border-radius: 8px;
                }}
            """)
            self.percentage_label.setStyleSheet(f"color: {COLORS['accent_success']};")

    def show_error(self, error_message: str):
        """Display error state"""
        self.task_label.setText("Loading Error")
        self.task_label.setStyleSheet(f"""
            color: {COLORS['text_error']};
            font-weight: 500;
        """)
        self.status_label.setText(error_message)
        self.status_label.setStyleSheet(f"color: {COLORS['text_error']};")
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {COLORS['text_error']};
                border-radius: 8px;
                background-color: {COLORS['background_secondary']};
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['text_error']};
                border-radius: 8px;
            }}
        """)

    def close_animation(self):
        """Clean up animation timers and signal completion"""
        # Emit signal to indicate loading screen should transition out
        self.loading_complete.emit()