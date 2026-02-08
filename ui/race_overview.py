"""
PyQt Race Overview Dashboard - Matches Electron.js styling
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QProgressBar, QGridLayout
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor

from .styles import COLORS
from .icons import create_icon_widget

class RaceHeaderCard(QWidget):
    """Race overview header matching Electron design"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header info grid
        header_layout = QGridLayout()

        # Race number and basic info
        race_info = QWidget()
        race_info_layout = QVBoxLayout(race_info)

        self.race_title = QLabel("Loading race data...")
        self.race_title.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: 24px;
                font-weight: bold;
            }}
        """)
        race_info_layout.addWidget(self.race_title)

        self.race_subtitle = QLabel("Analyzing horses...")
        self.race_subtitle.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_secondary']};
                font-size: 14px;
            }}
        """)
        race_info_layout.addWidget(self.race_subtitle)

        header_layout.addWidget(race_info, 0, 0)

        # Consensus pick
        consensus_widget = QWidget()
        consensus_layout = QVBoxLayout(consensus_widget)

        # Icon + text layout
        consensus_title_layout = QHBoxLayout()
        consensus_icon = create_icon_widget('trophy', 20)
        consensus_title_layout.addWidget(consensus_icon)

        consensus_title = QLabel("CONSENSUS PICK")
        consensus_title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLORS['text_primary']}; margin-left: 8px;")
        consensus_title_layout.addWidget(consensus_title)
        consensus_title_layout.addStretch()

        consensus_layout.addLayout(consensus_title_layout)

        self.consensus_horse = QLabel("Analyzing...")
        self.consensus_horse.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: 20px;
                font-weight: bold;
            }}
        """)
        consensus_layout.addWidget(self.consensus_horse)

        self.consensus_confidence = QLabel("0% confidence")
        self.consensus_confidence.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_secondary']};
                font-size: 12px;
            }}
        """)
        consensus_layout.addWidget(self.consensus_confidence)

        header_layout.addWidget(consensus_widget, 0, 1)

        # Market & pace info
        market_widget = QWidget()
        market_layout = QVBoxLayout(market_widget)

        # Icon + text layout for market
        market_title_layout = QHBoxLayout()
        market_icon = create_icon_widget('chart', 20)
        market_title_layout.addWidget(market_icon)

        market_title = QLabel("MARKET VIEW")
        market_title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLORS['text_primary']}; margin-left: 8px;")
        market_title_layout.addWidget(market_title)
        market_title_layout.addStretch()

        market_layout.addLayout(market_title_layout)

        self.market_info = QLabel("Loading market data...")
        self.market_info.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_secondary']};
                font-size: 12px;
            }}
        """)
        market_layout.addWidget(self.market_info)

        header_layout.addWidget(market_widget, 0, 2)

        layout.addLayout(header_layout)

        # Progress indicator
        progress_container = QWidget()
        progress_layout = QHBoxLayout(progress_container)

        self.status_label = QLabel("ML Analysis: Initializing...")
        self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        progress_layout.addWidget(self.status_label)

        progress_layout.addStretch()

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedWidth(200)
        progress_layout.addWidget(self.progress_bar)

        layout.addWidget(progress_container)

        # Styling
        self.setStyleSheet(f"""
            RaceHeaderCard {{
                background-color: {COLORS['background_medium']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)

    def update_race_info(self, race_data: dict):
        """Update with race information"""
        if not race_data:
            return

        # Update race title
        race_number = race_data.get('race_number', 1)
        distance = race_data.get('distance', 1650)
        horse_count = race_data.get('horse_count', 14)

        self.race_title.setText(f"Race {race_number}")
        self.race_subtitle.setText(f"{distance}m • {horse_count} runners")

    def update_predictions(self, predictions: list):
        """Update with ML predictions"""
        if not predictions or len(predictions) == 0:
            return

        # Find consensus pick (highest probability)
        consensus = max(predictions, key=lambda x: x['win_probability'])

        self.consensus_horse.setText(consensus['horse_name'])
        confidence_pct = consensus['win_probability'] * 100
        self.consensus_confidence.setText(f"{confidence_pct:.1f}% confidence")

        # Update progress
        self.progress_bar.setValue(100)
        self.status_label.setText("ML Analysis: Complete")

    def update_market_info(self, predictions: list):
        """Update market information"""
        if not predictions:
            return

        # Find odds range
        odds_list = [p['odds'] for p in predictions if p['odds'] > 0]
        if odds_list:
            favorite_odds = min(odds_list)
            longshot_odds = max(odds_list)
            self.market_info.setText(f"Favorite: {favorite_odds:.1f}/1 • Longshot: {longshot_odds:.1f}/1")
        else:
            self.market_info.setText("Market data unavailable")


class ProbabilityBar(QWidget):
    """Visual probability bar component"""

    def __init__(self, horse_name: str, probability: float, rank: int, parent=None):
        super().__init__(parent)
        self.horse_name = horse_name
        self.probability = probability
        self.rank = rank
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)

        # Rank icon and name
        rank_container = QWidget()
        rank_layout = QHBoxLayout(rank_container)
        rank_layout.setContentsMargins(0, 0, 0, 0)
        rank_layout.setSpacing(4)

        # Add medal icon for ranks 1-3
        if self.rank <= 3:
            medal_types = {1: 'gold_medal', 2: 'silver_medal', 3: 'bronze_medal'}
            medal_icon = create_icon_widget(medal_types[self.rank], 16)
            rank_layout.addWidget(medal_icon)
        else:
            # Number for ranks 4+
            rank_label = QLabel(str(self.rank))
            rank_label.setStyleSheet(f"""
                QLabel {{
                    color: {COLORS['text_muted']};
                    font-size: 11px;
                    font-weight: bold;
                }}
            """)
            rank_layout.addWidget(rank_label)

        # Horse name
        name_label = QLabel(self.horse_name[:12])
        name_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: 11px;
                font-weight: 500;
            }}
        """)
        rank_layout.addWidget(name_label)
        rank_layout.addStretch()

        rank_container.setFixedWidth(120)
        layout.addWidget(rank_container)

        # Probability bar
        bar_container = QWidget()
        bar_container.setFixedWidth(200)
        bar_layout = QHBoxLayout(bar_container)
        bar_layout.setContentsMargins(0, 0, 0, 0)

        bar = QFrame()
        bar.setFixedHeight(16)
        bar.setFixedWidth(int(200 * self.probability))

        # Color based on rank
        bar_colors = ['#f59e0b', '#9ca3af', '#dc2626']  # Gold, Gray, Red
        bar_color = bar_colors[min(self.rank - 1, len(bar_colors) - 1)]

        bar.setStyleSheet(f"""
            QFrame {{
                background-color: {bar_color};
                border-radius: 2px;
            }}
        """)
        bar_layout.addWidget(bar)

        # Fill remaining space
        bar_layout.addStretch()

        layout.addWidget(bar_container)

        # Percentage
        pct_label = QLabel(f"{self.probability * 100:.1f}%")
        pct_label.setFixedWidth(45)
        pct_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: 11px;
                font-weight: bold;
                font-family: 'Monaco', monospace;
            }}
        """)
        layout.addWidget(pct_label)