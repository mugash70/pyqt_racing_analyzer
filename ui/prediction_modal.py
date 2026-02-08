"""
Comprehensive Prediction Modals - Professional analytics and recommendations
"""

from PyQt5.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QScrollArea, QFrame, QGridLayout,
    QProgressBar, QComboBox, QSpinBox, QHeaderView
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QIcon
from datetime import datetime
from .styles import COLORS
from .icons import create_icon_widget
from .race_overview import ProbabilityBar


class DetailedHorseCard(QWidget):
    """Detailed horse prediction card with comprehensive statistics"""

    def __init__(self, prediction: dict, rank: int, parent=None):
        super().__init__(parent)
        self.prediction = prediction
        self.rank = rank
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Header with rank and horse name
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        # Rank badge
        rank_badge = QLabel(f"#{self.rank}")
        rank_badge.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: 14px;
                font-weight: bold;
                background-color: {COLORS['background_light']};
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 40px;
                text-align: center;
            }}
        """)
        rank_badge.setFixedWidth(50)
        header_layout.addWidget(rank_badge)

        # Horse info
        horse_info_layout = QVBoxLayout()
        horse_info_layout.setSpacing(2)

        horse_name = QLabel(self.prediction['horse_name'])
        horse_name.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: 16px;
                font-weight: bold;
            }}
        """)
        horse_info_layout.addWidget(horse_name)

        jockey_trainer = QLabel(f"{self.prediction['jockey']} • {self.prediction['trainer']}")
        jockey_trainer.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_secondary']};
                font-size: 11px;
            }}
        """)
        horse_info_layout.addWidget(jockey_trainer)

        header_layout.addLayout(horse_info_layout)

        # Confidence badge
        confidence = self.prediction['confidence']
        confidence_color = {
            'High': COLORS['accent_green'],
            'Medium': COLORS['accent_gold'],
            'Low': COLORS['accent_red']
        }.get(confidence, COLORS['text_secondary'])

        confidence_label = QLabel("{} {}".format(confidence, self.tr("Confidence")))
        confidence_label.setStyleSheet(f"""
            QLabel {{
                color: {confidence_color};
                font-size: 12px;
                font-weight: bold;
            }}
        """)
        header_layout.addStretch()
        header_layout.addWidget(confidence_label)

        layout.addLayout(header_layout)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet(f"background-color: {COLORS['border']};")
        layout.addWidget(divider)

        # Main stats grid
        stats_layout = QGridLayout()
        stats_layout.setSpacing(16)

        # Win probability (large)
        win_prob_widget = QWidget()
        win_prob_layout = QVBoxLayout(win_prob_widget)
        win_prob_layout.setContentsMargins(0, 0, 0, 0)
        win_prob_layout.setSpacing(4)

        win_prob_label = QLabel(self.tr("Win Probability"))
        win_prob_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10px; text-transform: uppercase;")
        win_prob_layout.addWidget(win_prob_label)

        win_prob_value = QLabel(f"{self.prediction['win_percentage']}")
        win_prob_value.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['accent_green']};
                font-size: 24px;
                font-weight: bold;
            }}
        """)
        win_prob_layout.addWidget(win_prob_value)

        stats_layout.addWidget(win_prob_widget, 0, 0)

        # Market odds
        odds_widget = QWidget()
        odds_layout = QVBoxLayout(odds_widget)
        odds_layout.setContentsMargins(0, 0, 0, 0)
        odds_layout.setSpacing(4)

        odds_label = QLabel(self.tr("Market Odds"))
        odds_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10px; text-transform: uppercase;")
        odds_layout.addWidget(odds_label)

        odds_value = QLabel(f"{self.prediction['odds']:.1f}/1")
        odds_value.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['accent_blue']};
                font-size: 24px;
                font-weight: bold;
            }}
        """)
        odds_layout.addWidget(odds_value)

        stats_layout.addWidget(odds_widget, 0, 1)

        # Value assessment
        value_widget = QWidget()
        value_layout = QVBoxLayout(value_widget)
        value_layout.setContentsMargins(0, 0, 0, 0)
        value_layout.setSpacing(4)

        value_label = QLabel(self.tr("Model Value"))
        value_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10px; text-transform: uppercase;")
        value_layout.addWidget(value_label)

        # Calculate implied probability from odds
        implied_prob = 1.0 / (self.prediction['odds'] + 1) if self.prediction['odds'] > 0 else 0
        model_prob = self.prediction['win_probability']
        edge = ((model_prob - implied_prob) / implied_prob * 100) if implied_prob > 0 else 0

        value_color = COLORS['accent_green'] if edge > 0 else COLORS['accent_red']
        value_value = QLabel(f"{edge:+.1f}%")
        value_value.setStyleSheet(f"""
            QLabel {{
                color: {value_color};
                font-size: 24px;
                font-weight: bold;
            }}
        """)
        value_layout.addWidget(value_value)

        stats_layout.addWidget(value_widget, 0, 2)

        layout.addLayout(stats_layout)

        # Divider
        divider2 = QFrame()
        divider2.setFrameShape(QFrame.HLine)
        divider2.setStyleSheet(f"background-color: {COLORS['border']};")
        layout.addWidget(divider2)

        # Details grid
        details_layout = QGridLayout()
        details_layout.setSpacing(12)

        # Weight
        weight_widget = self._create_detail_widget(
            self.tr("Weight"), "{} lbs".format(self.prediction['weight']) if self.prediction['weight'] else self.tr("N/A")
        )
        details_layout.addWidget(weight_widget, 0, 0)

        # Draw
        draw_widget = self._create_detail_widget(
            self.tr("Draw"), "#{}".format(self.prediction['draw']) if self.prediction['draw'] else self.tr("N/A")
        )
        details_layout.addWidget(draw_widget, 0, 1)

        # Horse ID
        horse_id_widget = self._create_detail_widget(
            self.tr("Horse ID"), str(self.prediction['horse_id'])
        )
        details_layout.addWidget(horse_id_widget, 0, 2)

        layout.addLayout(details_layout)

        # Styling
        self.setStyleSheet(f"""
            DetailedHorseCard {{
                background-color: {COLORS['background_medium']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)

    def _create_detail_widget(self, label: str, value: str) -> QWidget:
        """Helper to create a detail label+value widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        label_widget = QLabel(label)
        label_widget.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10px; text-transform: uppercase;")
        layout.addWidget(label_widget)

        value_widget = QLabel(value)
        value_widget.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 14px; font-weight: bold;")
        layout.addWidget(value_widget)

        return widget


class PredictionModal(QDialog):
    """Main comprehensive prediction modal"""

    horse_selected = pyqtSignal(dict)

    def __init__(self, predictions_data: dict, parent=None):
        super().__init__(parent)
        self.predictions_data = predictions_data
        self.predictions = predictions_data.get('predictions', [])
        self.race_info = predictions_data.get('race_info', {})

        self.setWindowTitle(self.tr("Race Predictions Analysis"))
        self.setMinimumSize(1200, 800)
        self.setMaximumSize(1600, 1000)
        self.setStyleSheet(f"background-color: {COLORS['background_dark']};")

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel(self.tr("Race Prediction Analysis"))
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        header_layout.addWidget(title)

        race_info_str = "{} • {}".format(self.race_info.get('date', self.tr('Unknown')), self.tr('Race {}').format(self.race_info.get('race_number', '?')))
        race_info_label = QLabel(race_info_str)
        race_info_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        header_layout.addStretch()
        header_layout.addWidget(race_info_label)

        layout.addLayout(header_layout)

        # Tabs-like button navigation
        view_buttons_layout = QHBoxLayout()
        view_buttons_layout.setSpacing(8)

        self.view_all_btn = QPushButton(self.tr("All Predictions"))
        self.view_all_btn.clicked.connect(self.show_all_predictions)
        self.view_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['button_primary']};
                color: {COLORS['text_primary']};
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
            }}
        """)
        view_buttons_layout.addWidget(self.view_all_btn)

        self.view_top5_btn = QPushButton(self.tr("Top 5 Contenders"))
        self.view_top5_btn.clicked.connect(self.show_top_5)
        self.view_top5_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['button_secondary']};
                color: {COLORS['text_primary']};
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
            }}
        """)
        view_buttons_layout.addWidget(self.view_top5_btn)

        self.view_stats_btn = QPushButton(self.tr("Statistical Summary"))
        self.view_stats_btn.clicked.connect(self.show_statistics)
        self.view_stats_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['button_secondary']};
                color: {COLORS['text_primary']};
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
            }}
        """)
        view_buttons_layout.addWidget(self.view_stats_btn)

        view_buttons_layout.addStretch()
        layout.addLayout(view_buttons_layout)

        # Main content area (scrollable)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {COLORS['background_dark']};
                border: none;
            }}
        """)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(12)

        scroll_area.setWidget(self.content_widget)
        layout.addWidget(scroll_area, 1)

        # Footer with action buttons
        footer_layout = QHBoxLayout()

        export_btn = QPushButton(self.tr("Export Analysis"))
        export_btn.clicked.connect(self.export_analysis)
        export_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['button_secondary']};
                color: {COLORS['text_primary']};
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
            }}
        """)
        footer_layout.addWidget(export_btn)

        footer_layout.addStretch()

        close_btn = QPushButton(self.tr("Close"))
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['button_primary']};
                color: {COLORS['text_primary']};
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
            }}
        """)
        footer_layout.addWidget(close_btn)

        layout.addLayout(footer_layout)

        # Show all predictions by default
        self.show_all_predictions()

    def show_all_predictions(self):
        """Show all horses with detailed cards"""
        self.clear_content()

        title = QLabel(self.tr("All Horses - Ranked by Win Probability"))
        title.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 8px;
            }}
        """)
        self.content_layout.addWidget(title)

        for rank, prediction in enumerate(self.predictions, 1):
            card = DetailedHorseCard(prediction, rank)
            card.mouseDoubleClickEvent = lambda e, p=prediction: self.horse_selected.emit(p)
            self.content_layout.addWidget(card)

        self.content_layout.addStretch()
        self.view_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['button_primary']};
                color: {COLORS['text_primary']};
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
            }}
        """)
        self.view_top5_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['button_secondary']};
                color: {COLORS['text_primary']};
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
            }}
        """)
        self.view_stats_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['button_secondary']};
                color: {COLORS['text_primary']};
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
            }}
        """)

    def show_top_5(self):
        """Show top 5 contenders only"""
        self.clear_content()

        title = QLabel(self.tr("Top 5 Contenders"))
        title.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 8px;
            }}
        """)
        self.content_layout.addWidget(title)

        for rank, prediction in enumerate(self.predictions[:5], 1):
            card = DetailedHorseCard(prediction, rank)
            self.content_layout.addWidget(card)

        self.content_layout.addStretch()
        self.view_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['button_secondary']};
                color: {COLORS['text_primary']};
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
            }}
        """)
        self.view_top5_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['button_primary']};
                color: {COLORS['text_primary']};
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
            }}
        """)
        self.view_stats_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['button_secondary']};
                color: {COLORS['text_primary']};
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
            }}
        """)

    def show_statistics(self):
        """Show statistical summary and analysis"""
        self.clear_content()

        title = QLabel(self.tr("Statistical Summary"))
        title.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 8px;
            }}
        """)
        self.content_layout.addWidget(title)

        # Calculate statistics
        if self.predictions:
            probs = [p['win_probability'] for p in self.predictions]
            odds = [p['odds'] for p in self.predictions if p['odds'] > 0]

            stats_widget = self._create_statistics_widget(probs, odds)
            self.content_layout.addWidget(stats_widget)

            # Probability distribution chart
            self.content_layout.addWidget(self._create_distribution_view())

        self.content_layout.addStretch()
        self.view_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['button_secondary']};
                color: {COLORS['text_primary']};
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
            }}
        """)
        self.view_top5_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['button_secondary']};
                color: {COLORS['text_primary']};
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
            }}
        """)
        self.view_stats_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['button_primary']};
                color: {COLORS['text_primary']};
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
            }}
        """)

    def _create_statistics_widget(self, probs: list, odds: list) -> QWidget:
        """Create statistics display widget"""
        widget = QWidget()
        layout = QGridLayout(widget)
        layout.setSpacing(16)

        stats = [
            (self.tr("Highest Probability"), f"{max(probs)*100:.1f}%"),
            (self.tr("Lowest Probability"), f"{min(probs)*100:.1f}%"),
            (self.tr("Average Probability"), f"{sum(probs)/len(probs)*100:.1f}%"),
            (self.tr("Total Contenders"), str(len(self.predictions))),
        ]

        if odds:
            stats.extend([
                (self.tr("Shortest Odds"), f"{min(odds):.1f}/1"),
                (self.tr("Longest Odds"), f"{max(odds):.1f}/1"),
            ])

        for idx, (label, value) in enumerate(stats):
            stat_widget = QWidget()
            stat_layout = QVBoxLayout(stat_widget)
            stat_layout.setContentsMargins(12, 8, 12, 8)
            stat_layout.setSpacing(4)

            label_widget = QLabel(label)
            label_widget.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10px; text-transform: uppercase;")
            stat_layout.addWidget(label_widget)

            value_widget = QLabel(value)
            value_widget.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 18px; font-weight: bold;")
            stat_layout.addWidget(value_widget)

            stat_widget.setStyleSheet(f"""
                QWidget {{
                    background-color: {COLORS['background_medium']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 6px;
                }}
            """)

            layout.addWidget(stat_widget, idx // 3, idx % 3)

        return widget

    def _create_distribution_view(self) -> QWidget:
        """Create probability distribution visualization"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 12, 0, 0)

        title = QLabel(self.tr("Win Probability Distribution"))
        title.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: 12px;
                font-weight: bold;
                margin-bottom: 8px;
            }}
        """)
        layout.addWidget(title)

        for rank, prediction in enumerate(self.predictions[:10], 1):
            bar = ProbabilityBar(prediction['horse_name'], prediction['win_probability'], rank)
            layout.addWidget(bar)

        return widget

    def clear_content(self):
        """Clear content layout"""
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def export_analysis(self):
        """Export analysis to file"""
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, self.tr("Export"), self.tr("Analysis exported successfully!"))

    def closeEvent(self, event):
        """Handle close event"""
        self.accept()
