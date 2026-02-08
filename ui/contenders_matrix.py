"""
PyQt Contenders Matrix - Matches Electron.js table styling
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame, QProgressBar
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from .styles import COLORS, CONTENDERS_TABLE_STYLE
from .icons import create_icon_widget

class ContendersMatrix(QWidget):
    """Horse analysis table matching Electron design"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header with icon
        header_container = QWidget()
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 8)

        target_icon = create_icon_widget('target', 20)
        header_layout.addWidget(target_icon)

        header = QLabel("WIN ANALYSIS - Top Contenders")
        header.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: 16px;
                font-weight: bold;
                margin-left: 8px;
            }}
        """)
        header_layout.addWidget(header)
        header_layout.addStretch()

        layout.addWidget(header_container)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['Horse', 'Model', 'Odds', 'Value', 'Edge'])

        # Configure table appearance
        self.table.setStyleSheet(CONTENDERS_TABLE_STYLE)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        # Set column widths
        header = self.table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(0, QHeaderView.Stretch)  # Horse name
            header.setSectionResizeMode(1, QHeaderView.Fixed)    # Model prob
            header.setSectionResizeMode(2, QHeaderView.Fixed)    # Odds
            header.setSectionResizeMode(3, QHeaderView.Fixed)    # Value
            header.setSectionResizeMode(4, QHeaderView.Fixed)    # Edge

        self.table.setColumnWidth(1, 80)
        self.table.setColumnWidth(2, 70)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 80)

        layout.addWidget(self.table)

        # Probability bars section
        self.probability_section = QWidget()
        prob_layout = QVBoxLayout(self.probability_section)

        prob_title = QLabel("WIN PROBABILITY DISTRIBUTION")
        prob_title.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: 14px;
                font-weight: bold;
                margin: 12px 0 8px 0;
            }}
        """)
        prob_layout.addWidget(prob_title)

        # Container for probability bars
        self.probability_container = QWidget()
        self.probability_layout = QVBoxLayout(self.probability_container)
        self.probability_layout.setSpacing(2)
        prob_layout.addWidget(self.probability_container)

        layout.addWidget(self.probability_section)

        # Loading indicator
        self.loading_label = QLabel("Analyzing predictions...")
        self.loading_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-style: italic;")
        layout.addWidget(self.loading_label)
        self.loading_label.hide()

    def update_predictions(self, predictions: list):
        """Update table with ML predictions"""
        if not predictions:
            self.table.setRowCount(0)
            return

        # Sort by probability and take top 5
        sorted_predictions = sorted(predictions, key=lambda x: x['win_probability'], reverse=True)[:5]

        self.table.setRowCount(len(sorted_predictions))

        for row, pred in enumerate(sorted_predictions):
            # Horse name with rank
            rank_number = row + 1
            if rank_number <= 3:
                # Use medal icons for top 3
                medal_types = {1: 'gold_medal', 2: 'silver_medal', 3: 'bronze_medal'}
                medal_icon = create_icon_widget(medal_types[rank_number], 16)
                # For table items, we'll use text since QTableWidgetItem doesn't support widgets directly
                horse_name = f"   {pred['horse_name']}"  # Add space for medal icon
            else:
                horse_name = f"{rank_number}. {pred['horse_name']}"

            horse_item = QTableWidgetItem(horse_name)
            horse_item.setForeground(QColor(COLORS['text_primary']))
            self.table.setItem(row, 0, horse_item)

            # Model probability
            prob_pct = f"{pred['win_probability'] * 100:.1f}%"
            prob_item = QTableWidgetItem(prob_pct)
            prob_item.setForeground(QColor(COLORS['accent_blue']))
            prob_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, prob_item)

            # Odds
            odds_text = f"{pred['odds']:.1f}" if pred['odds'] > 0 else "N/A"
            odds_item = QTableWidgetItem(odds_text)
            odds_item.setForeground(QColor(COLORS['text_secondary']))
            odds_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, odds_item)

            # Value calculation
            fair_odds = 1 / pred['win_probability'] if pred['win_probability'] > 0 else 0
            if pred['odds'] > 0 and fair_odds > 0:
                value_pct = ((pred['odds'] - fair_odds) / fair_odds) * 100
                value_text = f"{value_pct:+.1f}%"
                value_color = COLORS['accent_green'] if value_pct > 0 else COLORS['accent_red']
            else:
                value_text = "N/A"
                value_color = COLORS['text_muted']

            value_item = QTableWidgetItem(value_text)
            value_item.setForeground(QColor(value_color))
            value_item.setTextAlignment(0)
            self.table.setItem(row, 3, value_item)

            # Edge level
            if 'win_probability' in pred:
                prob = pred['win_probability']
                if prob > 0.25:
                    edge_text = "HIGH"
                    edge_color = COLORS['accent_green']
                elif prob > 0.15:
                    edge_text = "MEDIUM"
                    edge_color = COLORS['accent_gold']
                else:
                    edge_text = "LOW"
                    edge_color = COLORS['accent_red']
            else:
                edge_text = "N/A"
                edge_color = COLORS['text_muted']

            edge_item = QTableWidgetItem(edge_text)
            edge_item.setForeground(QColor(edge_color))
            edge_item.setTextAlignment(0)
            self.table.setItem(row, 4, edge_item)

        # Update probability bars
        self.update_probability_bars(sorted_predictions)

        # Hide loading indicator
        self.loading_label.hide()

    def update_probability_bars(self, predictions: list):
        """Update probability distribution visualization"""
        # Clear existing bars
        for i in reversed(range(self.probability_layout.count())):
            item = self.probability_layout.itemAt(i)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)

        if not predictions:
            return

        # Create probability bars for top 5 + others
        for i, pred in enumerate(predictions):
            bar = self.create_probability_bar(pred['horse_name'], pred['win_probability'], i + 1)
            self.probability_layout.addWidget(bar)

        # Add "others" bar
        remaining_prob = 1.0 - sum(p['win_probability'] for p in predictions)
        if remaining_prob > 0:
            others_bar = self.create_probability_bar("Others", remaining_prob, len(predictions) + 1, is_others=True)
            self.probability_layout.addWidget(others_bar)

    def create_probability_bar(self, horse_name: str, probability: float, rank: int, is_others: bool = False):
        """Create a single probability bar widget"""
        bar_widget = QWidget()
        bar_layout = QHBoxLayout(bar_widget)
        bar_layout.setContentsMargins(0, 2, 0, 2)

        # Horse name with rank
        if is_others:
            display_name = "Others"
        else:
            display_name = f"{horse_name[:12]}{'...' if len(horse_name) > 12 else ''}"

        # Create container for rank icon + name
        name_container = QWidget()
        name_layout = QHBoxLayout(name_container)
        name_layout.setContentsMargins(0, 0, 0, 0)
        name_layout.setSpacing(4)

        if not is_others and rank <= 3:
            # Add medal icon for top 3
            medal_types = {1: 'gold_medal', 2: 'silver_medal', 3: 'bronze_medal'}
            medal_icon = create_icon_widget(medal_types[rank], 14)
            name_layout.addWidget(medal_icon)
        elif not is_others:
            # Add number for ranks 4+
            rank_label = QLabel(str(rank))
            rank_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; font-weight: bold;")
            name_layout.addWidget(rank_label)

        # Add horse name
        name_text = QLabel(display_name)
        name_text.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: 11px;
                font-weight: 500;
            }}
        """)
        name_layout.addWidget(name_text)
        name_layout.addStretch()

        name_container.setFixedWidth(120)
        bar_layout.addWidget(name_container)

        # Progress bar
        progress = QProgressBar()
        progress.setRange(0, 100)
        progress.setValue(int(probability * 100))
        progress.setFixedWidth(200)
        progress.setFixedHeight(16)
        progress.setTextVisible(False)

        # Color based on rank
        if is_others:
            progress.setStyleSheet(f"""
                QProgressBar {{
                    border: 1px solid {COLORS['border']};
                    border-radius: 2px;
                    background-color: {COLORS['background_light']};
                }}
                QProgressBar::chunk {{
                    background-color: {COLORS['background_light']};
                    border-radius: 1px;
                }}
            """)
        else:
            bar_colors = [COLORS['accent_gold'], COLORS['text_muted'], COLORS['accent_red']]
            bar_color = bar_colors[min(rank - 1, len(bar_colors) - 1)]
            progress.setStyleSheet(f"""
                QProgressBar {{
                    border: 1px solid {COLORS['border']};
                    border-radius: 2px;
                    background-color: {COLORS['background_dark']};
                }}
                QProgressBar::chunk {{
                    background-color: {bar_color};
                    border-radius: 1px;
                }}
            """)

        bar_layout.addWidget(progress)

        # Percentage label
        pct_label = QLabel(f"{probability * 100:.1f}%")
        pct_label.setFixedWidth(45)
        pct_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: 11px;
                font-weight: bold;
                font-family: 'Monaco', monospace;
            }}
        """)
        bar_layout.addWidget(pct_label)

        return bar_widget

    def show_loading(self):
        """Show loading state"""
        self.loading_label.show()
        self.table.setRowCount(0)

        # Clear probability bars
        for i in reversed(range(self.probability_layout.count())):
            item = self.probability_layout.itemAt(i)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
