#!/usr/bin/env python3
"""
Modern Home Page - Professional Dashboard with Hero Sections
Displays welcome overview, top predictions, and quick actions
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel, QFrame,
    QComboBox, QPushButton, QGridLayout, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QDate, QTimer
from PyQt5.QtGui import QFont, QColor, QPixmap
from datetime import datetime
import sqlite3
import os
from typing import List, Dict, Tuple

from .styles import COLORS


class RaceCardWidget(QFrame):
    """Individual race card displaying horses"""
    
    view_predictions = pyqtSignal(int)
    
    def __init__(self, race_date: str, race_number: int, horses: list, parent=None):
        super().__init__(parent)
        self.race_date = race_date
        self.race_number = race_number
        self.horses = horses
        
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        self.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 16px;
                margin: 8px 0;
            }
        """)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(12, 12, 12, 8)
        
        race_label = QLabel(f"Race {self.race_number}")
        race_label.setFont(QFont("Arial", 16, QFont.Bold))
        race_label.setStyleSheet("color: #f8fafc;")
        
        date_label = QLabel(self.race_date)
        date_label.setFont(QFont("Arial", 10))
        date_label.setStyleSheet("color: #94a3b8;")
        
        header_layout.addWidget(race_label)
        header_layout.addStretch()
        header_layout.addWidget(date_label)
        
        view_btn = QPushButton("View Predictions")
        view_btn.setFont(QFont("Arial", 9))
        view_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: #f8fafc;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        view_btn.clicked.connect(lambda: self.view_predictions.emit(self.race_number))
        header_layout.addWidget(view_btn)
        
        layout.addLayout(header_layout)
        
        horse_frame = QFrame()
        horse_frame.setStyleSheet("background-color: transparent; border: none;")
        horse_layout = QVBoxLayout(horse_frame)
        horse_layout.setContentsMargins(12, 0, 12, 12)
        horse_layout.setSpacing(6)
        
        for i, horse in enumerate(self.horses[:15], 1):
            horse_row = self._create_horse_row(i, horse)
            horse_layout.addWidget(horse_row)
        
        layout.addWidget(horse_frame)
        self.setLayout(layout)
    
    def _create_horse_row(self, position: int, horse: dict) -> QFrame:
        """Create a single horse row"""
        row = QFrame()
        row.setStyleSheet("""
            QFrame {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 0px;
            }
            QFrame:hover {
                background-color: #1e293b;
                border: 1px solid #3b82f6;
            }
        """)
        row.setCursor(Qt.PointingHandCursor)
        
        layout = QHBoxLayout(row)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)
        
        pos_label = QLabel(str(position))
        pos_label.setFont(QFont("Arial", 10, QFont.Bold))
        pos_label.setFixedWidth(30)
        pos_label.setAlignment(Qt.AlignCenter)
        pos_label.setStyleSheet("color: #3b82f6;")
        
        name_label = QLabel(horse.get('horse_name', 'N/A'))
        name_label.setFont(QFont("Arial", 10))
        name_label.setStyleSheet("color: #f8fafc;")
        name_label.setMaximumWidth(150)
        
        jockey_label = QLabel(f"Jockey: {horse.get('jockey', 'N/A')}")
        jockey_label.setFont(QFont("Arial", 9))
        jockey_label.setStyleSheet("color: #cbd5e1;")
        
        weight_label = QLabel(f"Weight: {horse.get('weight', 'N/A')}")
        weight_label.setFont(QFont("Arial", 9))
        weight_label.setStyleSheet("color: #cbd5e1;")
        weight_label.setMaximumWidth(80)
        
        draw_label = QLabel(f"Draw: {horse.get('draw', 'N/A')}")
        draw_label.setFont(QFont("Arial", 9))
        draw_label.setStyleSheet("color: #64748b;")
        draw_label.setMaximumWidth(60)
        
        layout.addWidget(pos_label)
        layout.addWidget(name_label)
        layout.addWidget(jockey_label)
        layout.addWidget(weight_label)
        layout.addWidget(draw_label)
        layout.addStretch()
        
        return row


class MetricCard(QFrame):
    """Professional metric display card"""

    def __init__(self, title: str, value: str, subtitle: str = "", color: str = COLORS['accent_primary'], parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['background_primary']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 8px;
                padding: 20px;
            }}
            QFrame:hover {{
                border-color: {color};
                background-color: {COLORS['background_secondary']};
            }}
        """)
        self.init_ui(title, value, subtitle, color)

    def init_ui(self, title: str, value: str, subtitle: str, color: str):
        # Store values for updating existing layout
        self.current_title = title
        self.current_value = value
        self.current_subtitle = subtitle
        self.current_color = color

        # If layout doesn't exist, create it
        if not self.layout():
            layout = QVBoxLayout()
            layout.setSpacing(8)

            self.title_label = QLabel(title)
            self.title_label.setFont(QFont("Arial", 11))
            self.title_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-weight: 500;")
            layout.addWidget(self.title_label)

            self.value_label = QLabel(value)
            self.value_label.setFont(QFont("Arial", 24, QFont.Bold))
            self.value_label.setStyleSheet(f"color: {color};")
            layout.addWidget(self.value_label)

            if subtitle:
                self.subtitle_label = QLabel(subtitle)
                self.subtitle_label.setFont(QFont("Arial", 10))
                self.subtitle_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
                layout.addWidget(self.subtitle_label)

            layout.addStretch()
            self.setLayout(layout)
        else:
            # Update existing labels
            if hasattr(self, 'title_label'):
                self.title_label.setText(title)
            if hasattr(self, 'value_label'):
                self.value_label.setText(value)
                self.value_label.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: bold;")
            if hasattr(self, 'subtitle_label') and subtitle:
                self.subtitle_label.setText(subtitle)


class PredictionCard(QFrame):
    """Top prediction display card"""

    def __init__(self, race_num: int, horse_name: str, probability: float, confidence: float, parent=None):
        super().__init__(parent)
        self.race_num = race_num
        self.horse_name = horse_name
        self.probability = probability
        self.confidence = confidence

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['background_primary']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 8px;
                padding: 16px;
            }}
            QFrame:hover {{
                border-color: {COLORS['accent_primary']};
                background-color: {COLORS['background_secondary']};
            }}
        """)
        self.setCursor(Qt.PointingHandCursor)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Header
        header_layout = QHBoxLayout()
        race_label = QLabel(f"Race {self.race_num}")
        race_label.setFont(QFont("Arial", 12, QFont.Bold))
        race_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        header_layout.addWidget(race_label)

        header_layout.addStretch()

        prob_label = QLabel(f"{self.probability:.1f}%")
        prob_label.setFont(QFont("Arial", 14, QFont.Bold))
        prob_label.setStyleSheet(f"color: {COLORS['accent_success']};")
        header_layout.addWidget(prob_label)

        layout.addLayout(header_layout)

        # Horse name
        horse_label = QLabel(self.horse_name)
        horse_label.setFont(QFont("Arial", 16, QFont.Bold))
        horse_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(horse_label)

        # Confidence
        conf_label = QLabel(f"Confidence: {self.confidence:.1f}%")
        conf_label.setFont(QFont("Arial", 10))
        conf_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        layout.addWidget(conf_label)

        self.setLayout(layout)


class HomePage(QWidget):
    """Modern professional dashboard with hero sections"""

    view_predictions_requested = pyqtSignal(int)

    def __init__(self, db_path: str = None, parent=None):
        super().__init__(parent)
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'hkjc_races.db')
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

        # Initialize race predictor
        self.predictor = None
        self._init_predictor()

        # Store current predictions
        self.current_predictions: List[Tuple[int, str, float, float]] = []

        self.init_ui()
        self.load_dashboard_data()

        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.load_dashboard_data)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds

    def init_ui(self):
        """Initialize modern dashboard UI"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(32, 32, 32, 32)
        main_layout.setSpacing(24)

        # Hero Section
        hero_section = self._create_hero_section()
        main_layout.addWidget(hero_section)

        # Quick Actions Section
        actions_section = self._create_quick_actions()
        main_layout.addWidget(actions_section)

        # Metrics Row
        metrics_section = self._create_metrics_section()
        main_layout.addWidget(metrics_section)

        # Content Grid
        content_layout = QHBoxLayout()
        content_layout.setSpacing(24)

        # Left Column - Top Predictions
        left_column = self._create_predictions_column()
        content_layout.addWidget(left_column, 2)

        # Right Column - Market Overview
        right_column = self._create_market_overview()
        content_layout.addWidget(right_column, 1)

        main_layout.addLayout(content_layout)
        main_layout.addStretch()

        self.setLayout(main_layout)

    def _create_hero_section(self) -> QFrame:
        """Create welcoming hero section"""
        hero = QFrame()
        hero.setStyleSheet(f"""
            QFrame {{
                background: linear-gradient(135deg, {COLORS['accent_primary']} 0%, {COLORS['accent_success']} 100%);
                border-radius: 12px;
                padding: 32px;
                margin-bottom: 24px;
            }}
        """)

        layout = QVBoxLayout()
        layout.setSpacing(16)

        # Welcome message
        welcome = QLabel("Welcome to HKJC Racing Intelligence")
        welcome.setFont(QFont("Arial", 28, QFont.Bold))
        welcome.setStyleSheet(f"color: {COLORS['background_primary']};")
        layout.addWidget(welcome)

        # Subtitle
        subtitle = QLabel("Professional horse racing analysis powered by AI")
        subtitle.setFont(QFont("Arial", 16))
        subtitle.setStyleSheet(f"color: {COLORS['background_primary']}; opacity: 0.9;")
        layout.addWidget(subtitle)

        # Current status
        status_layout = QHBoxLayout()
        status_layout.setSpacing(16)

        self.live_indicator = QLabel("● LIVE")
        self.live_indicator.setProperty("class", "status-live")
        self.live_indicator.setFont(QFont("Arial", 12, QFont.Bold))
        status_layout.addWidget(self.live_indicator)

        self.last_update = QLabel("Data updated just now")
        self.last_update.setFont(QFont("Arial", 12))
        self.last_update.setStyleSheet(f"color: {COLORS['background_primary']}; opacity: 0.8;")
        status_layout.addWidget(self.last_update)

        status_layout.addStretch()
        layout.addLayout(status_layout)

        hero.setLayout(layout)
        return hero

    def _create_quick_actions(self) -> QFrame:
        """Create quick action buttons"""
        actions = QFrame()
        actions.setStyleSheet(f"background-color: transparent;")

        layout = QHBoxLayout()
        layout.setSpacing(16)

        # View Today's Races
        today_btn = QPushButton("Today's Races")
        today_btn.setFont(QFont("Arial", 13, QFont.Bold))
        today_btn.clicked.connect(self._show_today_races)
        layout.addWidget(today_btn)

        # View Predictions
        pred_btn = QPushButton("View Predictions")
        pred_btn.setFont(QFont("Arial", 13, QFont.Bold))
        pred_btn.clicked.connect(lambda: self.view_predictions_requested.emit(1))
        layout.addWidget(pred_btn)

        # Market Analysis
        market_btn = QPushButton("Market Analysis")
        market_btn.setFont(QFont("Arial", 13, QFont.Bold))
        market_btn.clicked.connect(self._show_market_analysis)
        layout.addWidget(market_btn)

        # Settings
        settings_btn = QPushButton("Settings")
        settings_btn.setProperty("class", "secondary")
        settings_btn.setFont(QFont("Arial", 13))
        settings_btn.clicked.connect(self._show_settings)
        layout.addWidget(settings_btn)

        layout.addStretch()
        actions.setLayout(layout)
        return actions

    def _create_metrics_section(self) -> QFrame:
        """Create key metrics display"""
        metrics = QFrame()
        metrics.setStyleSheet("background-color: transparent;")

        layout = QHBoxLayout()
        layout.setSpacing(16)

        # Create metric cards
        self.races_today = MetricCard("今日賽事", "--", "已安排賽事", COLORS['accent_primary'])
        layout.addWidget(self.races_today)

        self.total_horses = MetricCard("總馬匹數", "--", "數據庫中", COLORS['accent_success'])
        layout.addWidget(self.total_horses)

        self.active_predictions = MetricCard("已分析賽事", "--", "歷史數據庫", COLORS['accent_warning'])
        layout.addWidget(self.active_predictions)

        self.success_rate = MetricCard("模型狀態", "初始化...", "預測引擎", COLORS['chart_primary'])
        layout.addWidget(self.success_rate)

        metrics.setLayout(layout)
        return metrics

    def _create_predictions_column(self) -> QFrame:
        """Create top predictions column"""
        column = QFrame()
        column.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['background_primary']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 8px;
                padding: 24px;
            }}
        """)

        layout = QVBoxLayout()
        layout.setSpacing(16)

        # Header
        header = QLabel("Top Predictions")
        header.setFont(QFont("Arial", 18, QFont.Bold))
        header.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(header)

        subtitle = QLabel("Highest probability winners for today's races")
        subtitle.setFont(QFont("Arial", 12))
        subtitle.setStyleSheet(f"color: {COLORS['text_muted']};")
        layout.addWidget(subtitle)

        # Predictions container
        self.predictions_container = QVBoxLayout()
        self.predictions_container.setSpacing(12)

        # Load and display real predictions
        self._update_predictions_display()

        layout.addLayout(self.predictions_container)
        layout.addStretch()

        column.setLayout(layout)
        return column

    def _create_market_overview(self) -> QFrame:
        """Create market overview column"""
        column = QFrame()
        column.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['background_primary']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 8px;
                padding: 24px;
            }}
        """)

        layout = QVBoxLayout()
        layout.setSpacing(16)

        # Header
        header = QLabel("Market Overview")
        header.setFont(QFont("Arial", 18, QFont.Bold))
        header.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(header)

        # Market status
        status_card = QFrame()
        status_card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['background_secondary']};
                border-radius: 6px;
                padding: 16px;
            }}
        """)

        status_layout = QVBoxLayout()
        status_title = QLabel("Live Market Status")
        status_title.setFont(QFont("Arial", 14, QFont.Bold))
        status_title.setStyleSheet(f"color: {COLORS['text_primary']};")
        status_layout.addWidget(status_title)

        self.market_status = QLabel("● Waiting for data...")
        self.market_status.setFont(QFont("Arial", 12))
        self.market_status.setStyleSheet(f"color: {COLORS['text_muted']}; line-height: 1.6;")
        status_layout.addWidget(self.market_status)

        status_card.setLayout(status_layout)
        layout.addWidget(status_card)

        # Recent activity
        activity_card = QFrame()
        activity_card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['background_secondary']};
                border-radius: 6px;
                padding: 16px;
            }}
        """)

        activity_layout = QVBoxLayout()
        activity_title = QLabel("Recent Activity")
        activity_title.setFont(QFont("Arial", 14, QFont.Bold))
        activity_title.setStyleSheet(f"color: {COLORS['text_primary']};")
        activity_layout.addWidget(activity_title)

        self.activity_log = QLabel("• System initialized")
        self.activity_log.setFont(QFont("Arial", 11))
        self.activity_log.setStyleSheet(f"color: {COLORS['text_secondary']}; line-height: 1.6;")
        activity_layout.addWidget(self.activity_log)

        activity_card.setLayout(activity_layout)
        layout.addWidget(activity_card)

        layout.addStretch()

        column.setLayout(layout)
        return column

    def load_dashboard_data(self):
        """Load real dashboard data from database"""
        try:
            cursor = self.conn.cursor()

            # Update metrics
            cursor.execute("SELECT COUNT(DISTINCT race_number) FROM future_race_cards WHERE race_date = date('now')")
            races_count = cursor.fetchone()[0] or 0
            self.races_today.init_ui("今日賽事", str(races_count), "已安排賽事", COLORS['accent_primary'])

            cursor.execute("SELECT COUNT(*) FROM horses")
            horses_count = cursor.fetchone()[0] or 0
            self.total_horses.init_ui("總馬匹數", f"{horses_count:,}", "數據庫中", COLORS['accent_success'])

            # Calculate historical performance metrics
            self._update_performance_metrics(cursor)

            # Update predictions
            self._update_predictions_display()

            # Update last update time
            self.last_update.setText(f"最後更新: {datetime.now().strftime('%H:%M:%S')}")

        except Exception as e:
            print(f"Error loading dashboard data: {e}")

    def _show_today_races(self):
        """Navigate to today's races"""
        self.view_predictions_requested.emit(1)

    def _show_market_analysis(self):
        """Navigate to market analysis (would switch to analysis tab)"""
        pass

    def _show_settings(self):
        """Navigate to settings (would switch to settings tab)"""
        pass

    def _init_predictor(self):
        """Initialize the race predictor"""
        try:
            import sys
            import os
            parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            sys.path.insert(0, parent_dir)

            from engine.prediction.race_predictor import RacePredictor
            self.predictor = RacePredictor(self.db_path)
            print("Race predictor initialized successfully")
        except Exception as e:
            print(f"Error initializing race predictor: {e}")
            self.predictor = None

    def _load_real_predictions(self) -> List[Tuple[int, str, float, float]]:
        """Load real predictions for today's races"""
        if not self.predictor:
            print("Predictor not available")
            return []

        try:
            # Get today's races
            cursor = self.conn.cursor()
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute("""
                SELECT DISTINCT race_number, racecourse
                FROM future_race_cards
                WHERE race_date = ?
                ORDER BY race_number
            """, (today,))

            races = cursor.fetchall()
            if not races:
                print("No races found for today")
                return []

            all_predictions = []

            # Get predictions for each race
            for race in races:
                race_number = race['race_number']
                racecourse = race['racecourse']

                try:
                    predictions_result = self.predictor.predict_race(today, race_number, racecourse)

                    if 'predictions' in predictions_result:
                        for pred in predictions_result['predictions']:
                            horse_name = pred.get('horse_name', 'Unknown')
                            win_prob = pred.get('win_probability', 0) * 100  # Convert to percentage
                            confidence = pred.get('confidence', 50)  # Default confidence if not available

                            all_predictions.append((race_number, horse_name, win_prob, confidence))

                except Exception as e:
                    print(f"Error predicting race {race_number}: {e}")
                    continue

            # Sort by win probability and take top 5
            all_predictions.sort(key=lambda x: x[2], reverse=True)
            top_predictions = all_predictions[:5]

            print(f"Loaded {len(top_predictions)} real predictions")
            return top_predictions

        except Exception as e:
            print(f"Error loading real predictions: {e}")
            return []

    def _update_predictions_display(self):
        """Update the predictions display with current data"""
        # Clear existing predictions
        while self.predictions_container.count():
            item = self.predictions_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Load new predictions
        predictions = self._load_real_predictions()
        self.current_predictions = predictions

        if not predictions:
            # No predictions available - show message
            no_predictions_msg = QLabel("No races scheduled for today.\n\nPredictions will be available when races are announced.")
            no_predictions_msg.setFont(QFont("Arial", 14))
            no_predictions_msg.setStyleSheet("""
                QLabel {
                    color: #94a3b8;
                    padding: 40px;
                    text-align: center;
                    background-color: #1e293b;
                    border-radius: 8px;
                    border: 1px solid #334155;
                }
            """)
            no_predictions_msg.setAlignment(Qt.AlignCenter)
            self.predictions_container.addWidget(no_predictions_msg)
        else:
            # Add new prediction cards
            for race_num, horse_name, prob, conf in predictions:
                pred_card = PredictionCard(race_num, horse_name, prob, conf)
                pred_card.mousePressEvent = lambda e, r=race_num: self.view_predictions_requested.emit(r)
                self.predictions_container.addWidget(pred_card)

    def _update_performance_metrics(self, cursor):
        """Update performance metrics with real data"""
        try:
            # Get total races with results in database
            cursor.execute("""
                SELECT COUNT(DISTINCT race_date || '-' || race_number) as total_races
                FROM race_results
            """)
            total_races = cursor.fetchone()[0] or 0

            # Update the metric cards with real data
            self.active_predictions.init_ui("已分析賽事", f"{total_races:,}", "歷史數據庫", COLORS['accent_warning'])
            self.success_rate.init_ui("模型狀態", "就緒", "預測引擎運行中", COLORS['chart_primary'])

            print(f"Updated metrics: {total_races:,} races analyzed, model ready")

        except Exception as e:
            print(f"Error updating performance metrics: {e}")
            # Fallback to default values
            self.active_predictions.init_ui("已分析賽事", "0", "歷史數據庫", COLORS['accent_warning'])
            self.success_rate.init_ui("模型狀態", "就緒", "預測引擎運行中", COLORS['chart_primary'])

    def closeEvent(self, event):
        """Clean up timers on close"""
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
        super().closeEvent(event)
