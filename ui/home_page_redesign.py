"""
Redesigned Home Page - Modern Prediction Dashboard (Dark Theme)
Features:
- Date Selector
- Racecourse Selector (ST/HV)
- Generate Predictions Button
- Future Race Cards with ML Rankings
- Filter by Race
- Detailed Prediction Reasons
- Accuracy Statistics
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QScrollArea, 
    QGridLayout, QProgressBar, QTabWidget, QGroupBox, QDateEdit,
    QTextEdit, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QDate, QTimer, QThread
from PyQt5.QtGui import QFont, QColor, QPalette
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Dark theme colors matching main.py
DARK_COLORS = {
    'background_primary': '#0d1117',
    'background_secondary': '#161b22',
    'background_tertiary': '#21262d',
    'text_primary': '#c9d1d9',
    'text_secondary': '#8b949e',
    'text_muted': '#6e7681',
    'accent_primary': '#58a6ff',
    'accent_success': '#238636',
    'accent_warning': '#d29922',
    'accent_error': '#f85149',
    'border_light': '#30363d',
}


class PredictionCard(QFrame):
    """Individual prediction card for a horse."""
    
    def __init__(self, horse_name: str, rank: int, win_prob: float, 
                 confidence: float, odds: float = None, parent=None):
        super().__init__(parent)
        self.horse_name = horse_name
        self.rank = rank
        self.win_prob = win_prob
        self.confidence = confidence
        
        self.setFixedHeight(80)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {DARK_COLORS['background_primary']};
                border: 1px solid {DARK_COLORS['border_light']};
                border-radius: 8px;
                padding: 8px;
            }}
            QFrame:hover {{
                border-color: {DARK_COLORS['accent_primary']};
                background-color: {DARK_COLORS['background_secondary']};
            }}
        """)
        
        self.init_ui(odds)
    
    def init_ui(self, odds: float):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(16)
        
        # Rank badge
        rank_badge = QLabel(f"#{self.rank}")
        rank_badge.setFixedWidth(40)
        rank_badge.setAlignment(Qt.AlignCenter)
        rank_badge.setFont(QFont("Arial", 14, QFont.Bold))
        if self.rank == 1:
            rank_badge.setStyleSheet(f"color: #FFD700; background-color: transparent;")
        elif self.rank <= 3:
            rank_badge.setStyleSheet(f"color: #C0C0C0; background-color: transparent;")
        else:
            rank_badge.setStyleSheet(f"color: {DARK_COLORS['text_secondary']}; background-color: transparent;")
        layout.addWidget(rank_badge)
        
        # Horse name
        name_label = QLabel(self.horse_name)
        name_label.setFont(QFont("Arial", 12, QFont.Bold))
        name_label.setStyleSheet(f"color: {DARK_COLORS['text_primary']};")
        name_label.setMinimumWidth(150)
        layout.addWidget(name_label)
        
        # Win probability bar
        prob_layout = QVBoxLayout()
        prob_layout.setSpacing(2)
        
        prob_label = QLabel(f"{self.win_prob:.1f}%")
        prob_label.setFont(QFont("Arial", 11, QFont.Bold))
        prob_label.setStyleSheet(f"color: {DARK_COLORS['accent_success']};")
        prob_layout.addWidget(prob_label)
        
        prob_bar = QProgressBar()
        prob_bar.setFixedWidth(100)
        prob_bar.setFixedHeight(6)
        prob_bar.setMinimum(0)
        prob_bar.setMaximum(100)
        prob_bar.setValue(int(self.win_prob))
        prob_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {DARK_COLORS['background_secondary']};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {DARK_COLORS['accent_success']};
                border-radius: 3px;
            }}
        """)
        prob_layout.addWidget(prob_bar)
        layout.addLayout(prob_layout)
        
        # Confidence
        conf_label = QLabel(f"信心: {self.confidence:.0%}")
        conf_label.setFont(QFont("Arial", 10))
        conf_label.setStyleSheet(f"color: {DARK_COLORS['text_muted']};")
        conf_label.setFixedWidth(70)
        layout.addWidget(conf_label)
        
        # Odds
        if odds:
            odds_label = QLabel(f"賠率: {odds:.1f}")
            odds_label.setFont(QFont("Arial", 10))
            odds_label.setStyleSheet(f"color: {DARK_COLORS['text_secondary']};")
            layout.addWidget(odds_label)
        
        layout.addStretch()
    
    def update_data(self, horse_name: str, rank: int, win_prob: float, 
                   confidence: float, odds: float = None):
        """Update card with new data."""
        self.horse_name = horse_name
        self.rank = rank
        self.win_prob = win_prob
        self.confidence = confidence
        
        # Update UI (clear and rebuild)
        for i in reversed(range(self.layout().count())):
            item = self.layout().takeAt(i)
            if item.widget():
                item.widget().deleteLater()
        
        self.init_ui(odds)


class RaceCardWidget(QFrame):
    """Race card showing horses and their predictions."""
    
    view_details = pyqtSignal(str, int, str)  # race_date, race_number, racecourse
    
    def __init__(self, race_date: str, race_number: int, racecourse: str,
                 race_info: Dict = None, parent=None):
        super().__init__(parent)
        self.race_date = race_date
        self.race_number = race_number
        self.racecourse = racecourse
        self.race_info = race_info or {}
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {DARK_COLORS['background_primary']};
                border: 1px solid {DARK_COLORS['border_light']};
                border-radius: 12px;
                padding: 16px;
            }}
        """)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header_layout = QHBoxLayout()
        
        race_title_text = f"第{self.race_number}場 • {self.racecourse}"
        if self.race_info.get('time'):
            race_title_text += f" ({self.race_info['time']})"
        
        race_title = QLabel(race_title_text)
        race_title.setFont(QFont("Arial", 14, QFont.Bold))
        race_title.setStyleSheet(f"color: {DARK_COLORS['text_primary']};")
        header_layout.addWidget(race_title)
        
        header_layout.addStretch()
        
        # Distance and Class
        if self.race_info:
            info_text = f"{self.race_info.get('distance', '')}米 • {self.race_info.get('race_class', '')}"
            if self.race_info.get('going'):
                info_text += f" • {self.race_info['going']}"
            
            info_label = QLabel(info_text)
            info_label.setFont(QFont("Arial", 10))
            info_label.setStyleSheet(f"color: {DARK_COLORS['text_muted']};")
            header_layout.addWidget(info_label)
        
        # View Details Button
        view_btn = QPushButton("查看詳情")
        view_btn.setFixedWidth(100)
        view_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a73e8;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #1557b0;
            }
        """)
        view_btn.clicked.connect(lambda: self.view_details.emit(
            self.race_date, self.race_number, self.racecourse
        ))
        header_layout.addWidget(view_btn)
        
        layout.addLayout(header_layout)
        
        # Horses container
        # self.horses_container = QVBoxLayout()
        # self.horses_container.setSpacing(8)
        # layout.addLayout(self.horses_container)
        
        # Footer with stats
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        
        self.status_label = QLabel("就緒")
        self.status_label.setFont(QFont("Arial", 9))
        self.status_label.setStyleSheet(f"color: {DARK_COLORS['text_muted']};")
        footer_layout.addWidget(self.status_label)
        
        layout.addLayout(footer_layout)
    
    def load_predictions(self, predictions: List[Dict]):
        """Load predictions into the race card."""
        # # Clear existing
        # for i in reversed(range(self.horses_container.count())):
        #     item = self.horses_container.takeAt(i)
        #     if item.widget():
        #         item.widget().deleteLater()
        
        if not predictions:
            no_pred = QLabel("暫無預測數據")
            no_pred.setFont(QFont("Arial", 10))
            no_pred.setStyleSheet(f"color: {DARK_COLORS['text_muted']};")
            no_pred.setAlignment(Qt.AlignCenter)
            # self.horses_container.addWidget(no_pred)
            self.status_label.setText("無數據")
            return
        
        # Add top 5 horses
        for i, pred in enumerate(predictions[:5]):
            card = PredictionCard(
                horse_name=pred.get('horse_name', 'Unknown'),
                rank=i+1,
                win_prob=pred.get('win_probability', 0),
                confidence=pred.get('confidence', 0),
                odds=pred.get('current_odds')
            )
            # self.horses_container.addWidget(card)
        
        # Update status
        top_pick = predictions[0] if predictions else None
        if top_pick:
            win_prob = top_pick.get('win_probability', 0)
            self.status_label.setText(f"首選: {top_pick.get('horse_name', '')} ({win_prob:.1f}%)")
    
    def set_loading(self, loading: bool):
        """Set loading state."""
        if loading:
            self.status_label.setText("載入預測中...")
            self.status_label.setStyleSheet(f"color: {DARK_COLORS['accent_warning']};")


class AccuracyMetricsWidget(QFrame):
    """Display accuracy metrics."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {DARK_COLORS['background_primary']};
                border: 1px solid {DARK_COLORS['border_light']};
                border-radius: 8px;
                padding: 0;
            }}
        """)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Title
        title = QLabel("模型表現 (最近30天)")
        title.setFont(QFont("Arial", 11, QFont.Bold))
        title.setStyleSheet(f"color: {DARK_COLORS['text_primary']};")
        layout.addWidget(title)
        
        # Metrics grid
        metrics_layout = QGridLayout()
        metrics_layout.setSpacing(8)
        
        self.metrics_labels = {}
        
        metrics = [
            ("勝率", "win_rate", "%"),
            ("位置率", "place_rate", "%"),
            ("回報率", "roi", "%"),
            ("平均賠率", "avg_odds", ""),
            ("預測次數", "predictions", ""),
            ("賽事數", "races", "")
        ]
        
        for i, (label, key, unit) in enumerate(metrics):
            # Label
            lbl = QLabel(label)
            lbl.setFont(QFont("Arial", 9))
            lbl.setStyleSheet(f"color: {DARK_COLORS['text_muted']};")
            metrics_layout.addWidget(lbl, i // 3 * 2, i % 3)
            
            # Value
            val_lbl = QLabel("--")
            val_lbl.setFont(QFont("Arial", 16, QFont.Bold))
            val_lbl.setStyleSheet(f"color: {DARK_COLORS['accent_primary']};")
            metrics_layout.addWidget(val_lbl, i // 3 * 2 + 1, i % 3)
            
            self.metrics_labels[key] = val_lbl
        
        layout.addLayout(metrics_layout)
    
    def update_metrics(self, metrics: Dict):
        """Update metrics display."""
        for key, label in self.metrics_labels.items():
            value = metrics.get(key, 0)
            if key in ['win_rate', 'place_rate', 'roi']:
                label.setText(f"{value:.1f}%")
                # Color coding
                if key == 'roi':
                    if value > 0:
                        label.setStyleSheet("color: #10b981; font-size: 16px; font-weight: bold;")
                    elif value < -10:
                        label.setStyleSheet("color: #ef4444; font-size: 16px; font-weight: bold;")
                    else:
                        label.setStyleSheet(f"color: {DARK_COLORS['accent_primary']}; font-size: 16px; font-weight: bold;")
            else:
                label.setText(f"{value}")
        
        # Update based on thresholds
        roi = metrics.get('roi', 0)
        if roi > 10:
            self.metrics_labels['roi'].setToolTip("優秀回報率")
        elif roi < -10:
            self.metrics_labels['roi'].setToolTip("回報率欠佳 - 請檢視策略")


class HorseRankingWidget(QFrame):
    """Horse rankings based on ML scores."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {DARK_COLORS['background_primary']};
                border: 1px solid {DARK_COLORS['border_light']};
                border-radius: 8px;
                padding: 0;
            }}
        """)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Title
        title = QLabel("馬匹排名")
        title.setFont(QFont("Arial", 11, QFont.Bold))
        title.setStyleSheet(f"color: {DARK_COLORS['text_primary']};")
        layout.addWidget(title)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["排名", "馬匹", "評分", "練馬師", "近績"])
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: transparent;
                border: none;
                font-size: 10px;
            }}
            QHeaderView::section {{
                background-color: {DARK_COLORS['background_secondary']};
                color: {DARK_COLORS['text_primary']};
                padding: 4px;
                font-weight: 600;
                font-size: 10px;
            }}
        """)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setRowCount(0)
        layout.addWidget(self.table)
        
        # Refresh button
        refresh_btn = QPushButton("重新整理")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a73e8;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #1557b0;
            }
        """)
        layout.addWidget(refresh_btn)
    
    def load_rankings(self, rankings: List[Dict]):
        """Load horse rankings into table."""
        self.table.setRowCount(len(rankings))
        
        for i, horse in enumerate(rankings):
            # Rank
            rank_item = QTableWidgetItem(str(i + 1))
            rank_item.setBackground(QColor("#1e293b") if i < 3 else QColor("#0f172a"))
            if i == 0:
                rank_item.setForeground(QColor("#FFD700"))
            elif i < 3:
                rank_item.setForeground(QColor("#C0C0C0"))
            self.table.setItem(i, 0, rank_item)
            
            # Horse name
            name_item = QTableWidgetItem(horse.get('name', 'Unknown'))
            name_item.setForeground(QColor("#f8fafc"))
            self.table.setItem(i, 1, name_item)
            
            # Score
            score_item = QTableWidgetItem(f"{horse.get('score', 0):.1f}")
            score_item.setForeground(QColor("#10b981"))
            self.table.setItem(i, 2, score_item)
            
            # Trainer
            trainer_item = QTableWidgetItem(horse.get('trainer', 'Unknown'))
            trainer_item.setForeground(QColor("#94a3b8"))
            self.table.setItem(i, 3, trainer_item)
            
            # Form
            form_item = QTableWidgetItem(horse.get('recent_form', 'N/A'))
            form_item.setForeground(QColor("#64748b"))
            self.table.setItem(i, 4, form_item)
        
        self.table.resizeColumnsToContents()


class PredictionWorker(QThread):
    """Background worker for batch predictions."""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, db_path: str, race_date: str, racecourse: str):
        super().__init__()
        self.db_path = db_path
        self.race_date = race_date
        self.racecourse = racecourse
        
    def run(self):
        try:
            from engine.prediction.enhanced_predictor import EnhancedRacePredictor
            from engine.verification.accuracy_tracker import AccuracyTracker
            
            predictor = EnhancedRacePredictor(self.db_path)
            tracker = AccuracyTracker(self.db_path)
            
            predictions = predictor.predict_multiple_races(self.race_date, self.racecourse)
            
            # Log predictions to database for future retrieval (non-critical)
            # Logging failures don't prevent showing predictions
            logging_errors = []
            for race_pred in predictions:
                race_info = race_pred.get('race_info', {})
                # Normalize date to YYYY-MM-DD format for database storage
                race_date = race_info.get('date')
                if race_date and isinstance(race_date, str) and ' ' in race_date:
                    race_date = race_date.split(' ')[0]  # Remove timestamp if present
                
                race_number = race_info.get('number')
                racecourse = race_info.get('track')
                
                for i, horse_pred in enumerate(race_pred.get('predictions', [])):
                    try:
                        tracker.log_prediction({
                            'race_date': race_date,
                            'race_number': race_number,
                            'racecourse': racecourse,
                            'horse_name': horse_pred.get('horse_name'),
                            'horse_number': horse_pred.get('horse_number'),
                            'predicted_rank': i + 1,
                            'win_probability': horse_pred.get('win_probability', 0) / 100.0,
                            'place_probability': horse_pred.get('place_probability', 0) / 100.0,
                            'confidence': horse_pred.get('confidence', 0),
                            'current_odds': horse_pred.get('current_odds'),
                            'value_pct': horse_pred.get('value_pct')
                        })
                    except Exception as log_err:
                        # Log but don't fail - predictions are more important than logging
                        logging_errors.append(f"Failed to log {horse_pred.get('horse_name')}: {str(log_err)}")
                        print(f"[INFO] Logging error (non-critical): {log_err}")
            
            # Always emit predictions even if logging fails
            self.finished.emit(predictions)
            
            # Report logging errors if any occurred
            if logging_errors:
                print(f"[INFO] {len(logging_errors)} predictions generated but {len(logging_errors)} logging errors occurred")
        except Exception as e:
            print(f"PredictionWorker error: {e}")
            import traceback
            traceback.print_exc()
            self.error.emit(str(e))


class BottomCollapsibleWidget(QWidget):
    """Widget at bottom with collapsible sections."""
    
    def __init__(self, metrics_widget, rankings_widget, parent=None):
        super().__init__(parent)
        self.metrics_widget = metrics_widget
        self.rankings_widget = rankings_widget
        self.metrics_expanded = False
        self.rankings_expanded = False
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Hidden toggle buttons (still exist but not visible)
        self.metrics_toggle = QPushButton()
        self.metrics_toggle.setVisible(False)
        self.metrics_toggle.clicked.connect(self.toggle_metrics)
        
        self.rankings_toggle = QPushButton()
        self.rankings_toggle.setVisible(False)
        self.rankings_toggle.clicked.connect(self.toggle_rankings)
        
        # Content area - both widgets side by side, always visible
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)
        
        self.metrics_widget.setVisible(True)
        self.rankings_widget.setVisible(True)
        content_layout.addWidget(self.metrics_widget, 1)
        content_layout.addWidget(self.rankings_widget, 1)
        
        layout.addLayout(content_layout)
    
    def toggle_metrics(self):
        self.metrics_expanded = not self.metrics_expanded
        self.metrics_widget.setVisible(self.metrics_expanded)
        self.metrics_toggle.setText(f"{'▼' if self.metrics_expanded else '▶'} 模型表現")
        self.update_content_visibility()
    
    def toggle_rankings(self):
        self.rankings_expanded = not self.rankings_expanded
        self.rankings_widget.setVisible(self.rankings_expanded)
        self.rankings_toggle.setText(f"{'▼' if self.rankings_expanded else '▶'} 馬匹排名")
        self.update_content_visibility()
    
    def update_content_visibility(self):
        # Show content area if either is expanded
        self.content_widget.setVisible(self.metrics_expanded or self.rankings_expanded)


class RedesignedHomePage(QWidget):
    """Redesigned home page with prediction capabilities."""
    
    view_race_details = pyqtSignal(str, int, str)  # race_date, race_number, racecourse
    
    def __init__(self, db_path: str = None, parent=None):
        super().__init__(parent)
        
        if db_path is None:
            # Use absolute path from the project root
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(script_dir, 'database', 'hkjc_races.db')
        
        # Verify database exists
        if not os.path.exists(db_path):
            # Try alternative path
            alt_path = os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'hkjc_races.db')
            if os.path.exists(alt_path):
                db_path = alt_path
        
        self.db_path = db_path
        
        self.selected_date = datetime.now().strftime('%Y-%m-%d')
        self.selected_course = "ST"
        self.predictor = None
        
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        """Initialize the redesigned UI."""
        # Main vertical layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Top Section - Controls (outside scroll, always visible)
        self.create_control_panel(main_layout)
        
        # Middle Section - Race Cards Grid (with its own scroll area)
        self.create_race_cards_scroll_section(main_layout)
        
        # Bottom Section - Collapsible widgets (always visible at bottom)
        self.create_bottom_section(main_layout)
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.load_data)
        self.refresh_timer.start(60000)  # Refresh every minute
    
    def create_control_panel(self, parent_layout: QVBoxLayout):
        """Create the control panel with date, course selectors and predict button."""
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {DARK_COLORS['background_secondary']};
                border: 1px solid {DARK_COLORS['border_light']};
                border-radius: 8px;
            }}
        """)
        
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(16)
        
        # Date selector
        date_layout = QVBoxLayout()
        date_layout.setSpacing(2)
        
        date_label = QLabel("日期")
        date_label.setFont(QFont("Arial", 9))
        date_label.setStyleSheet(f"color: {DARK_COLORS['text_muted']};")
        date_layout.addWidget(date_label)
        
        self.date_combo = QComboBox()
        self.date_combo.setFixedWidth(180)
        self.date_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {DARK_COLORS['background_primary']};
                color: {DARK_COLORS['text_primary']};
                border: 1px solid {DARK_COLORS['border_light']};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
            }}
        """)
        self.date_combo.currentIndexChanged.connect(self.on_date_changed)
        date_layout.addWidget(self.date_combo)
        
        layout.addLayout(date_layout)
        
        # Racecourse selector
        course_layout = QVBoxLayout()
        course_layout.setSpacing(2)
        
        course_label = QLabel("馬場")
        course_label.setFont(QFont("Arial", 9))
        course_label.setStyleSheet(f"color: {DARK_COLORS['text_muted']};")
        course_layout.addWidget(course_label)
        
        self.course_combo = QComboBox()
        self.course_combo.addItems(["沙田 (ST)", "跑馬地 (HV)"])
        self.course_combo.setFixedWidth(120)
        self.course_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {DARK_COLORS['background_primary']};
                color: {DARK_COLORS['text_primary']};
                border: 1px solid {DARK_COLORS['border_light']};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
            }}
        """)
        self.course_combo.currentIndexChanged.connect(self.on_course_changed)
        course_layout.addWidget(self.course_combo)
        
        layout.addLayout(course_layout)
        
        # Race filter
        race_layout = QVBoxLayout()
        race_layout.setSpacing(2)
        
        race_label = QLabel("篩選")
        race_label.setFont(QFont("Arial", 9))
        race_label.setStyleSheet(f"color: {DARK_COLORS['text_muted']};")
        race_layout.addWidget(race_label)
        
        self.race_combo = QComboBox()
        self.race_combo.addItem("全部賽事")
        self.race_combo.setFixedWidth(90)
        self.race_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {DARK_COLORS['background_primary']};
                color: {DARK_COLORS['text_primary']};
                border: 1px solid {DARK_COLORS['border_light']};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
            }}
        """)
        race_layout.addWidget(self.race_combo)
        
        layout.addLayout(race_layout)
        
        layout.addStretch()
        
        # Generate Predictions Button
        self.predict_btn = QPushButton("生成預測")
        self.predict_btn.setFixedSize(140, 36)
        self.predict_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DARK_COLORS['accent_success']};
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: #059669;
            }}
            QPushButton:disabled {{
                background-color: #475569;
            }}
        """)
        self.predict_btn.clicked.connect(self.generate_predictions)
        layout.addWidget(self.predict_btn)
        
        # Refresh Button
        refresh_btn = QPushButton("重新整理")
        refresh_btn.setFixedSize(100, 36)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a73e8;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1557b0;
            }
        """)
        refresh_btn.clicked.connect(self.load_data)
        layout.addWidget(refresh_btn)
        
        parent_layout.addWidget(panel)
    
    def create_race_cards_scroll_section(self, parent_layout: QVBoxLayout):
        """Create the race cards section with its own scroll area."""
        # Create a container for race cards with header and scroll
        container = QWidget()
        container.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Header
        header_layout = QHBoxLayout()
        
        self.races_label = QLabel("賽事卡")
        self.races_label.setFont(QFont("Arial", 13, QFont.Bold))
        self.races_label.setStyleSheet(f"color: {DARK_COLORS['text_primary']};")
        header_layout.addWidget(self.races_label)
        
        self.races_count_label = QLabel()
        self.races_count_label.setFont(QFont("Arial", 9))
        self.races_count_label.setStyleSheet(f"color: {DARK_COLORS['text_muted']};")
        header_layout.addWidget(self.races_count_label)
        
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Race cards scroll area - this is the scrollable part
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: transparent; border: none;")
        
        self.races_container = QWidget()
        self.races_container.setStyleSheet("background-color: transparent;")
        self.races_layout = QGridLayout(self.races_container)
        self.races_layout.setSpacing(12)
        
        scroll.setWidget(self.races_container)
        layout.addWidget(scroll, 1)  # Give it stretch factor to take available space
        
        parent_layout.addWidget(container, 1)  # Add to main layout with stretch
    
    def create_bottom_section(self, parent_layout: QVBoxLayout):
        """Create bottom section with collapsible metrics and rankings."""
        # Create the widgets
        self.metrics_widget = AccuracyMetricsWidget()
        self.rankings_widget = HorseRankingWidget()
        
        # Create the collapsible container - no fixed height, always show content
        self.bottom_widget = BottomCollapsibleWidget(self.metrics_widget, self.rankings_widget)
        self.bottom_widget.setStyleSheet("background-color: #0d1117;")
        parent_layout.addWidget(self.bottom_widget)
    
    def load_data(self):
        """Load initial data."""
        self.load_dates()
        self.load_races()
        self.load_metrics()
        self.load_rankings_data()
    
    def load_rankings_data(self):
        """Load horse rankings data from future race cards."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            

            print("=------------",self.selected_date)
            # Get horses from future race cards for the selected date
            cursor.execute("""
                SELECT horse_name, trainer, jockey, recent_results, rating
                FROM future_race_cards
                WHERE DATE(race_date) = ?
                ORDER BY rating DESC
                LIMIT 20
            """, (self.selected_date,))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Map to widget format
            formatted_rankings = []
            for i, row in enumerate(rows):
                formatted_rankings.append({
                    'name': row['horse_name'] or 'Unknown',
                    'score': float(row['rating'] or 0),
                    'trainer': row['trainer'] or 'N/A',
                    'recent_form': row['recent_results'] or 'N/A'
                })
            
            self.rankings_widget.load_rankings(formatted_rankings)
            
        except Exception as e:
            print(f"Error loading rankings: {e}")
            self.rankings_widget.load_rankings([])
    
    def load_dates(self):
        """Load available dates into dropdown with availability indicators."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get all dates from fixtures
            cursor.execute("""
                SELECT DISTINCT DATE(race_date) as race_date 
                FROM fixtures 
                ORDER BY DATE(race_date) DESC 
                LIMIT 14
            """)
            
            fixture_dates = [row['race_date'] for row in cursor.fetchall()]
            
            # Get dates that have race card data
            cursor.execute("""
                SELECT DISTINCT DATE(race_date) as race_date 
                FROM future_race_cards 
                ORDER BY DATE(race_date) DESC
            """)
            
            racecard_dates = {row['race_date'] for row in cursor.fetchall()}
            conn.close()
            
            if fixture_dates:
                current_idx = self.date_combo.currentIndex()
                self.date_combo.clear()
                
                for d in fixture_dates:
                    # Format display
                    try:
                        date_obj = datetime.strptime(d, '%Y-%m-%d')
                        today = datetime.now().date()
                        if date_obj.date() == today:
                            date_str = f"今日 ({d})"
                        elif date_obj.date() == today + timedelta(days=1):
                            date_str = f"明日 ({d})"
                        else:
                            date_str = date_obj.strftime('%Y-%m-%d (%a)')
                    except:
                        date_str = d
                    
                    # Add availability indicator and only show available dates
                    if d in racecard_dates:
                        display = f"✓ {date_str}"
                        self.date_combo.addItem(display, d)
                    else:
                        # Skip dates without racecard data
                        continue
                
                # Restore selection or select the most recent available date
                if current_idx >= 0 and current_idx < self.date_combo.count():
                    self.date_combo.setCurrentIndex(current_idx)
                elif self.date_combo.count() > 0:
                    self.date_combo.setCurrentIndex(0)
        except Exception as e:
            print(f"Error loading dates: {e}")
    
    def load_races(self):
        """Load races for selected date."""
        # Clear existing race cards
        for i in reversed(range(self.races_layout.count())):
            item = self.races_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
        
        race_date = self.selected_date
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # First check what tables exist and their schema
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row['name'] for row in cursor.fetchall()]
            
            races = []
            
            # Try future_race_cards first (most reliable)
            if 'future_race_cards' in tables:
                # Handle racecourse mapping to be robust (matches ST/HV or Sha Tin/Happy Valley)
                if self.selected_course == "ST":
                    cursor.execute("""
                        SELECT DISTINCT race_number, racecourse, race_distance, race_class, track_going, race_time
                        FROM future_race_cards
                        WHERE DATE(race_date) = ? 
                        AND (racecourse LIKE '%ST%' OR racecourse LIKE '%Sha Tin%' OR racecourse LIKE '%沙田%')
                        ORDER BY race_number
                    """, (race_date,))
                elif self.selected_course == "HV":
                    cursor.execute("""
                        SELECT DISTINCT race_number, racecourse, race_distance, race_class, track_going, race_time
                        FROM future_race_cards
                        WHERE DATE(race_date) = ? 
                        AND (racecourse LIKE '%HV%' OR racecourse LIKE '%Happy Valley%' OR racecourse LIKE '%跑馬地%')
                        ORDER BY race_number
                    """, (race_date,))
                else:
                    # Default case - all courses
                    cursor.execute("""
                        SELECT DISTINCT race_number, racecourse, race_distance, race_class, track_going, race_time
                        FROM future_race_cards
                        WHERE DATE(race_date) = ?
                        ORDER BY race_number
                    """, (race_date,))
                
                races = cursor.fetchall()

            # If no races, try fixtures table
            if not races and 'fixtures' in tables:
                cursor.execute("PRAGMA table_info(fixtures)")
                columns = [row['name'] for row in cursor.fetchall()]
                
                # Handle racecourse filtering for fixtures table
                if self.selected_course == "ST":
                    cursor.execute("""
                        SELECT DISTINCT race_date, racecourse, distance as race_distance, race_class, expected_races
                        FROM fixtures 
                        WHERE DATE(race_date) = ? 
                        AND (racecourse LIKE '%ST%' OR racecourse LIKE '%Sha Tin%' OR racecourse LIKE '%沙田%')
                    """, (race_date,))
                elif self.selected_course == "HV":
                    cursor.execute("""
                        SELECT DISTINCT race_date, racecourse, distance as race_distance, race_class, expected_races
                        FROM fixtures 
                        WHERE DATE(race_date) = ? 
                        AND (racecourse LIKE '%HV%' OR racecourse LIKE '%Happy Valley%' OR racecourse LIKE '%跑馬地%')
                    """, (race_date,))
                else:
                    cursor.execute("""
                        SELECT DISTINCT race_date, racecourse, distance as race_distance, race_class, expected_races
                        FROM fixtures 
                        WHERE DATE(race_date) = ?
                    """, (race_date,))
                
                fixture_races = cursor.fetchall()
                for fr in fixture_races:
                    # Convert sqlite3.Row to dict
                    fr_dict = dict(fr)
                    
                    # Generate race numbers from 1 to expected_races
                    expected = 8  # Default
                    if 'expected_races' in fr_dict and fr_dict['expected_races']:
                        try:
                            expected = int(fr_dict['expected_races'])
                        except:
                            pass
                    
                    for race_num in range(1, min(expected + 1, 12)):
                        races.append({
                            'race_number': race_num,
                            'racecourse': fr_dict.get('racecourse', 'Unknown'),
                            'race_distance': fr_dict.get('race_distance', 'Unknown'),
                            'race_class': fr_dict.get('race_class', 'Unknown'),
                            'track_going': 'Unknown',
                            'race_time': None
                        })
            
            conn.close()
            
            if not races:
                no_races = QLabel("找不到賽事。\n\n請嘗試在設定標籤中重新整理數據。")
                no_races.setFont(QFont("Arial", 12))
                no_races.setStyleSheet(f"color: {DARK_COLORS['text_muted']};")
                no_races.setAlignment(Qt.AlignCenter)
                self.races_layout.addWidget(no_races, 0, 0)
                
                self.races_count_label.setText("(0 場賽事)")
                return
            
            # Update race filter
            current_race_idx = self.race_combo.currentIndex()
            self.race_combo.clear()
            self.race_combo.addItem("全部賽事")
            
            for race in races:
                # Convert sqlite3.Row to dict if needed
                if hasattr(race, 'keys'):
                    race = dict(race)
                self.race_combo.addItem(f"第{race['race_number']}場", race['race_number'])
            
            if current_race_idx >= 0 and current_race_idx < self.race_combo.count():
                self.race_combo.setCurrentIndex(current_race_idx)
            
            # Create race cards
            for i, race in enumerate(races):
                # Convert sqlite3.Row to dict if needed
                if hasattr(race, 'keys'):
                    race = dict(race)
                
                race_info = {
                    'distance': race.get('race_distance', 'Unknown'),
                    'race_class': race.get('race_class', 'Unknown'),
                    'going': race.get('track_going', 'Unknown'),
                    'time': race.get('race_time', '')
                }
                
                card = RaceCardWidget(
                    race_date=race_date,
                    race_number=race['race_number'],
                    racecourse=race['racecourse'],
                    race_info=race_info
                )
                card.view_details.connect(self.on_view_details)
                
                self.races_layout.addWidget(card, i // 2, i % 2)
                
                # Check for existing predictions in database
                self.load_card_predictions(card)
            
            self.races_count_label.setText(f"({len(races)} 場賽事)")
            
        except Exception as e:
            import traceback
            print(f"[DEBUG] Error loading races: {e}")
            print(traceback.format_exc())
            
            no_races = QLabel(f"載入賽事時出錯:\n{str(e)}")
            no_races.setFont(QFont("Arial", 10))
            no_races.setStyleSheet(f"color: {DARK_COLORS['accent_error']};")
            no_races.setAlignment(Qt.AlignCenter)
            self.races_layout.addWidget(no_races, 0, 0)
    
    def load_card_predictions(self, card: RaceCardWidget):
        """Load existing predictions for a specific race card."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Normalize the date for comparison - extract just the date part if there's a timestamp
            normalized_date = card.race_date
            if normalized_date and ' ' in str(normalized_date):
                normalized_date = str(normalized_date).split(' ')[0]
            
            # Build racecourse condition based on selected course
            # Use simple equality check to avoid binding issues
            course_value = card.racecourse  # Use the exact value from the card
            
            # Try multiple date formats to ensure we find matching predictions
            cursor.execute("""
                SELECT horse_name, horse_number, predicted_rank, predicted_win_prob, confidence, current_odds
                FROM prediction_log
                WHERE (race_date = ? OR DATE(race_date) = ?) AND race_number = ? AND racecourse = ?
                ORDER BY predicted_rank
            """, (normalized_date, normalized_date, card.race_number, course_value))
            
            rows = cursor.fetchall()
            
            # If no results with exact match, try without racecourse filter
            if not rows:
                cursor.execute("""
                    SELECT horse_name, horse_number, predicted_rank, predicted_win_prob, confidence, current_odds
                    FROM prediction_log
                    WHERE (race_date = ? OR DATE(race_date) = ?) AND race_number = ?
                    ORDER BY predicted_rank
                """, (normalized_date, normalized_date, card.race_number))
                rows = cursor.fetchall()
            
            conn.close()
            
            if rows:
                predictions = []
                for row in rows:
                    predictions.append({
                        'horse_name': row['horse_name'],
                        'horse_number': row['horse_number'],
                        'win_probability': row['predicted_win_prob'],
                        'confidence': row['confidence'],
                        'current_odds': row['current_odds']
                    })
                card.load_predictions(predictions)
            else:
                card.set_loading(False)
                card.status_label.setText("無已儲存預測")
                
        except Exception as e:
            print(f"Error loading card predictions: {e}")
            card.set_loading(False)

    def load_metrics(self):
        """Load accuracy metrics."""
        try:
            # Check if requests is available as it might be needed by some imports
            try:
                import requests
            except ImportError:
                print("[ERROR] requests module is not installed. Please run: pip install requests")
                self.metrics_widget.update_metrics({
                    'win_rate': 0, 'place_rate': 0, 'roi': 0, 'avg_odds': 0, 'predictions': 0, 'races': 0
                })
                return

            # Try to get metrics from verification module
            from engine.verification.accuracy_tracker import AccuracyTracker
            
            tracker = AccuracyTracker(self.db_path)
            thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            metrics = tracker.get_period_summary(thirty_days_ago)
            
            self.metrics_widget.update_metrics({
                'win_rate': metrics.win_rate,
                'place_rate': metrics.place_rate,
                'roi': metrics.roi_percent,
                'avg_odds': metrics.average_odds,
                'predictions': metrics.total_predictions,
                'races': metrics.total_races
            })
            
        except Exception as e:
            print(f"Error loading metrics: {e}")
            # Use default values
            self.metrics_widget.update_metrics({
                'win_rate': 0,
                'place_rate': 0,
                'roi': 0,
                'avg_odds': 0,
                'predictions': 0,
                'races': 0
            })
    
    def on_date_changed(self, index: int):
        """Handle date selection change."""
        if index >= 0:
            self.selected_date = self.date_combo.itemData(index)
            self.load_races()
    
    def on_course_changed(self, index: int):
        """Handle racecourse selection change."""
        courses = ["ST", "HV"]
        if index >= 0:
            self.selected_course = courses[index]
            self.load_races()
    
    def on_view_details(self, race_date: str, race_number: int, racecourse: str):
        """Handle view details request."""
        self.view_race_details.emit(race_date, race_number, racecourse)
    
    def generate_predictions(self):
        """Generate predictions for all races on selected date."""
        self.predict_btn.setEnabled(False)
        self.predict_btn.setText("生成中...")
        
        # Use background worker to prevent UI freeze
        self.prediction_worker = PredictionWorker(self.db_path, self.selected_date, self.selected_course)
        self.prediction_worker.finished.connect(self.on_predictions_finished)
        self.prediction_worker.error.connect(self.on_predictions_error)
        self.prediction_worker.start()
        
    def on_predictions_finished(self, predictions):
        """Handle finished predictions."""
        # Update race cards with predictions
        for i in range(self.races_layout.count()):
            item = self.races_layout.itemAt(i)
            if item.widget() and isinstance(item.widget(), RaceCardWidget):
                card = item.widget()
                race_num = card.race_number
                
                # Find matching predictions
                race_preds = None
                for pred in predictions:
                    if pred.get('race_info', {}).get('number') == race_num:
                        race_preds = pred.get('predictions', [])
                        break
                
                if race_preds:
                    card.load_predictions(race_preds)
        
        self.predict_btn.setText("已生成!")
        self.predict_btn.setEnabled(True)
        
        QTimer.singleShot(2000, lambda: self.predict_btn.setText("生成預測"))
        
    def on_predictions_error(self, error_msg):
        """Handle prediction error."""
        print(f"Error generating predictions: {error_msg}")
        self.predict_btn.setEnabled(True)
        self.predict_btn.setText("生成預測")
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.warning(self, "預測錯誤", f"生成預測失敗: {error_msg}")
    
    def closeEvent(self, event):
        """Clean up on close."""
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
        super().closeEvent(event)
