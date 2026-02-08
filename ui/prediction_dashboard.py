"""
Detailed Prediction Modal - Shows complete prediction with reasons and analysis.
Features:
- Horse predictions with rankings
- Detailed reasoning for each horse
- Confidence scores
- Value analysis
- Risk assessment
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QScrollArea, QFrame, QPushButton, QTabWidget, QWidget, QTextEdit,
    QGridLayout, QProgressBar, QGroupBox, QComboBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPixmap
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional


class SingleRacePredictionWorker(QThread):
    """Background worker for single race prediction."""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, db_path: str, race_date: str, race_number: int, racecourse: str):
        super().__init__()
        self.db_path = db_path
        self.race_date = race_date
        self.race_number = race_number
        self.racecourse = racecourse
        
    def run(self):
        try:
            from engine.prediction.enhanced_predictor import EnhancedRacePredictor
            predictor = EnhancedRacePredictor(self.db_path)
            result = predictor.predict_race(self.race_date, self.race_number, self.racecourse)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class PredictionDetailModal(QDialog):
    """Detailed prediction modal with full reasoning."""
    
    def __init__(self, race_date: str, race_number: int, racecourse: str = "ST",
                 parent=None, db_path: str = None):
        super().__init__(parent)
        self.race_date = race_date
        self.race_number = race_number
        self.racecourse = racecourse
        
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
        
        self.setWindowTitle(f"第{race_number}場預測 - {race_date}")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet("background-color: #0f172a;")
        
        self.init_ui()
        self.load_predictions()
    
    def init_ui(self):
        """Initialize the modal UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel(f"第{self.race_number}場 • {self.racecourse} • {self.race_date}")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setStyleSheet("color: #f8fafc;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Status label
        self.status_label = QLabel("載入預測中...")
        self.status_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        header_layout.addWidget(self.status_label)
        
        layout.addLayout(header_layout)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { 
                border: 1px solid #334155; 
                background-color: #0f172a;
            }
            QTabBar::tab { 
                background-color: #1e293b; 
                color: #cbd5e1; 
                padding: 10px 20px;
                border: 1px solid #334155;
                font-weight: 600;
            }
            QTabBar::tab:selected { 
                background-color: #334155; 
                color: #f8fafc;
                border-bottom: 2px solid #3b82f6;
            }
        """)
        layout.addWidget(self.tabs)
        
        # Tab 1: Predictions Table
        self.create_predictions_tab()
        
        # Tab 2: Detailed Reasons
        self.create_reasons_tab()
        
        # Tab 3: Analysis
        self.create_analysis_tab()
        
        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        
        close_btn = QPushButton("關閉")
        close_btn.setFixedSize(100, 40)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: #f8fafc;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(close_btn)
        
        layout.addLayout(footer_layout)
    
    def create_predictions_tab(self):
        """Create the predictions table tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Summary header
        summary_layout = QHBoxLayout()
        
        self.win_pick_label = QLabel("首選: --")
        self.win_pick_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.win_pick_label.setStyleSheet("color: #10b981;")
        summary_layout.addWidget(self.win_pick_label)
        
        summary_layout.addStretch()
        
        self.confidence_label = QLabel("信心度: --")
        self.confidence_label.setFont(QFont("Arial", 12))
        self.confidence_label.setStyleSheet("color: #94a3b8;")
        summary_layout.addWidget(self.confidence_label)
        
        layout.addLayout(summary_layout)
        
        # Table
        self.pred_table = QTableWidget()
        self.pred_table.setColumnCount(10)
        self.pred_table.setHorizontalHeaderLabels([
            "排名", "馬匹", "勝率", "位置率", "信心度", 
            "賠率", "價值", "風險", "騎師", "練馬師"
        ])
        self.pred_table.setStyleSheet("""
            QTableWidget {
                background-color: #0f172a;
                border: 1px solid #334155;
                gridline-color: #334155;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 10px 8px;
                color: #f8fafc;
            }
            QHeaderView::section {
                background-color: #1e293b;
                color: #f8fafc;
                padding: 10px;
                font-weight: 600;
                border: 1px solid #334155;
            }
        """)
        self.pred_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.pred_table)
        
        # Legend
        legend_layout = QHBoxLayout()
        
        legend_items = [
            ("✓ 冠軍", "#10b981"),
            ("~ 前三", "#f59e0b"),
            ("✗ 其他", "#64748b")
        ]
        
        for text, color in legend_items:
            lbl = QLabel(text)
            lbl.setFont(QFont("Arial", 10))
            lbl.setStyleSheet(f"color: {color};")
            legend_layout.addWidget(lbl)
        
        legend_layout.addStretch()
        layout.addLayout(legend_layout)
        
        self.tabs.addTab(tab, "預測")
    
    def create_reasons_tab(self):
        """Create the detailed reasons tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Horse selector
        selector_layout = QHBoxLayout()
        
        selector_label = QLabel("選擇馬匹:")
        selector_label.setFont(QFont("Arial", 12))
        selector_label.setStyleSheet("color: #94a3b8;")
        selector_layout.addWidget(selector_label)
        
        self.horse_selector = QComboBox()
        self.horse_selector.setStyleSheet("""
            QComboBox {
                background-color: #1e293b;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 8px 12px;
                min-width: 200px;
            }
        """)
        self.horse_selector.currentIndexChanged.connect(self.on_horse_selected)
        selector_layout.addWidget(self.horse_selector)
        
        selector_layout.addStretch()
        layout.addLayout(selector_layout)
        
        # Reasons content
        self.reasons_content = QTextEdit()
        self.reasons_content.setReadOnly(True)
        self.reasons_content.setStyleSheet("""
            QTextEdit {
                background-color: #0f172a;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 16px;
                font-family: 'SF Mono', 'Consolas', monospace;
                font-size: 12px;
                line-height: 1.6;
            }
        """)
        layout.addWidget(self.reasons_content)
        
        self.tabs.addTab(tab, "詳細理由")
    
    def create_analysis_tab(self):
        """Create the analysis tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Race info
        info_group = QGroupBox("賽事資訊")
        info_group.setStyleSheet(f"""
            QGroupBox {{
                color: #f8fafc;
                font-weight: 600;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 16px;
                margin-top: 8px;
            }}
        """)
        
        info_layout = QGridLayout(info_group)
        
        info_items = [
            ("距離:", "distance", ""),
            ("班次:", "race_class", ""),
            ("賽道:", "track", ""),
            ("場地:", "going", ""),
            ("獎金:", "prize_money", ""),
            ("參賽馬數:", "field_size", ""),
        ]
        
        for i, (label, key, default) in enumerate(info_items):
            lbl = QLabel(label)
            lbl.setStyleSheet("color: #94a3b8;")
            info_layout.addWidget(lbl, i // 3 * 2, i % 3)
            
            val = QLabel(default)
            val.setStyleSheet("color: #f8fafc; font-weight: 600;")
            val.setObjectName(key)
            info_layout.addWidget(val, i // 3 * 2 + 1, i % 3)
        
        layout.addWidget(info_group)
        
        # Model info
        model_group = QGroupBox("模型資訊")
        model_group.setStyleSheet(f"""
            QGroupBox {{
                color: #f8fafc;
                font-weight: 600;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 16px;
                margin-top: 8px;
            }}
        """)
        
        model_layout = QVBoxLayout(model_group)
        
        self.model_info = QLabel("模型: 增強版 v2.0\n校準: 冪律\n特徵: 100+")
        self.model_info.setStyleSheet("color: #94a3b8; font-family: monospace;")
        model_layout.addWidget(self.model_info)
        
        layout.addWidget(model_group)
        layout.addStretch()
        
        self.tabs.addTab(tab, "賽事分析")
    
    def load_predictions(self):
        """Load predictions from the predictor."""
        self.status_label.setText("計算預測中...")
        self.status_label.setStyleSheet("color: #3b82f6;")
        
        self.worker = SingleRacePredictionWorker(self.db_path, self.race_date, self.race_number, self.racecourse)
        self.worker.finished.connect(self.on_predictions_finished)
        self.worker.error.connect(self.on_predictions_error)
        self.worker.start()
        
    def on_predictions_finished(self, result):
        """Handle finished predictions."""
        if 'error' in result:
            self.status_label.setText(f"錯誤: {result['error']}")
            self.status_label.setStyleSheet("color: #ef4444;")
            return
        
        self.result = result
        self.predictions = result.get('predictions', [])
        self.race_info = result.get('race_info', {})
        
        # Update UI
        self.update_predictions_table()
        self.update_horse_selector()
        self.update_race_info()
        
        # Update status
        if self.predictions:
            self.status_label.setText(f"已載入 {len(self.predictions)} 個預測")
            self.status_label.setStyleSheet("color: #10b981;")
        else:
            self.status_label.setText("無可用預測")
            self.status_label.setStyleSheet("color: #f59e0b;")
            
    def on_predictions_error(self, error_msg):
        """Handle prediction error."""
        self.status_label.setText(f"錯誤: {error_msg}")
        self.status_label.setStyleSheet("color: #ef4444;")
        print(f"Error loading predictions: {error_msg}")
    
    def update_predictions_table(self):
        """Update the predictions table."""
        self.pred_table.setRowCount(len(self.predictions))
        
        for row_idx, pred in enumerate(self.predictions):
            # Rank
            rank_item = QTableWidgetItem(str(row_idx + 1))
            rank_item.setForeground(QColor("#f8fafc"))
            rank_item.setBackground(QColor("#1e293b"))
            self.pred_table.setItem(row_idx, 0, rank_item)
            
            # Horse name
            name_item = QTableWidgetItem(pred.get('horse_name', '未知'))
            name_item.setForeground(QColor("#f8fafc"))
            name_item.setBackground(QColor("#0f172a"))
            self.pred_table.setItem(row_idx, 1, name_item)
            
            # Win probability
            win_prob = pred.get('win_probability', 0)
            win_item = QTableWidgetItem(f"{win_prob:.1f}%")
            win_item.setForeground(QColor("#10b981"))
            win_item.setBackground(QColor("#0f172a"))
            self.pred_table.setItem(row_idx, 2, win_item)
            
            # Place probability
            place_prob = pred.get('place_probability', 0)
            place_item = QTableWidgetItem(f"{place_prob:.1f}%")
            place_item.setForeground(QColor("#3b82f6"))
            place_item.setBackground(QColor("#0f172a"))
            self.pred_table.setItem(row_idx, 3, place_item)
            
            # Confidence
            conf = pred.get('confidence', 0) * 100
            conf_item = QTableWidgetItem(f"{conf:.0f}%")
            conf_item.setForeground(QColor("#f59e0b"))
            conf_item.setBackground(QColor("#0f172a"))
            self.pred_table.setItem(row_idx, 4, conf_item)
            
            # Odds
            odds = pred.get('current_odds')
            if odds and odds > 0:
                odds_item = QTableWidgetItem(f"{odds:.1f}")
            else:
                odds_item = QTableWidgetItem("N/A")
            odds_item.setForeground(QColor("#94a3b8"))
            odds_item.setBackground(QColor("#0f172a"))
            self.pred_table.setItem(row_idx, 5, odds_item)
            
            # Value
            value = pred.get('value_pct')
            if value is not None:
                value_item = QTableWidgetItem(f"{value:+.0f}%")
                if value > 10:
                    value_item.setForeground(QColor("#10b981"))
                elif value < -10:
                    value_item.setForeground(QColor("#ef4444"))
                else:
                    value_item.setForeground(QColor("#94a3b8"))
                value_item.setBackground(QColor("#0f172a"))
            else:
                value_item = QTableWidgetItem("N/A")
                value_item.setForeground(QColor("#64748b"))
                value_item.setBackground(QColor("#0f172a"))
            self.pred_table.setItem(row_idx, 6, value_item)
            
            # Risk
            risk = pred.get('risk_score', 0)
            risk_item = QTableWidgetItem(f"{risk:.0f}")
            if risk > 60:
                risk_item.setForeground(QColor("#ef4444"))
            elif risk > 40:
                risk_item.setForeground(QColor("#f59e0b"))
            else:
                risk_item.setForeground(QColor("#10b981"))
            risk_item.setBackground(QColor("#0f172a"))
            self.pred_table.setItem(row_idx, 7, risk_item)
            
            # Jockey
            jockey_item = QTableWidgetItem(pred.get('jockey', 'N/A'))
            jockey_item.setForeground(QColor("#94a3b8"))
            jockey_item.setBackground(QColor("#0f172a"))
            self.pred_table.setItem(row_idx, 8, jockey_item)
            
            # Trainer
            trainer_item = QTableWidgetItem(pred.get('trainer', 'N/A'))
            trainer_item.setForeground(QColor("#94a3b8"))
            trainer_item.setBackground(QColor("#0f172a"))
            self.pred_table.setItem(row_idx, 9, trainer_item)
        
        # Update summary
        if self.predictions:
            top = self.predictions[0]
            self.win_pick_label.setText(f"首選: {top.get('horse_name', '未知')}")
            conf = top.get('confidence', 0) * 100
            self.confidence_label.setText(f"信心度: {conf:.0f}%")
        
        self.pred_table.resizeColumnsToContents()
    
    def update_horse_selector(self):
        """Update the horse selector dropdown."""
        self.horse_selector.clear()
        
        for pred in self.predictions:
            rank = self.predictions.index(pred) + 1
            self.horse_selector.addItem(f"#{rank} - {pred.get('horse_name', '未知')}", pred)
        
        # Select first horse by default
        if self.predictions:
            self.on_horse_selected(0)
    
    def on_horse_selected(self, index: int):
        """Handle horse selection for detailed reasons."""
        if index < 0 or index >= len(self.predictions):
            return
        
        pred = self.predictions[index]
        reasons = pred.get('detailed_reasons', {})
        
        # Build detailed text
        text = []
        text.append("=" * 60)
        text.append(f"預測 #{index + 1}: {pred.get('horse_name', '未知').upper()}")
        text.append("=" * 60)
        text.append("")
        
        # Basic info
        text.append("基本資訊")
        text.append("-" * 40)
        text.append(f"馬匹編號: {pred.get('horse_number', 'N/A')}")
        text.append(f"騎師: {pred.get('jockey', 'N/A')}")
        text.append(f"練馬師: {pred.get('trainer', 'N/A')}")
        text.append(f"負磅: {pred.get('weight', 'N/A')}")
        text.append(f"檔位: {pred.get('draw', 'N/A')}")
        text.append("")
        
        # Prediction metrics
        text.append("預測指標")
        text.append("-" * 40)
        text.append(f"勝出機率: {pred.get('win_probability', 0):.2f}%")
        text.append(f"位置機率: {pred.get('place_probability', 0):.2f}%")
        text.append(f"信心度: {pred.get('confidence', 0) * 100:.0f}%")
        
        odds = pred.get('current_odds')
        if odds and odds > 0:
            text.append(f"現時賠率: {odds:.1f}")
        
        value = pred.get('value_pct')
        if value is not None:
            text.append(f"價值: {value:+.1f}%")
        
        text.append("")
        
        # Risk assessment
        text.append("風險評估")
        text.append("-" * 40)
        text.append(f"風險評分: {pred.get('risk_score', 0):.0f}/100")
        text.append(f"建議: {pred.get('risk_recommendation', 'N/A')}")
        text.append("")
        
        # Positive factors
        positive = reasons.get('positive_factors', [])
        if positive:
            text.append("✓ 正面因素")
            text.append("-" * 40)
            for factor in positive:
                text.append(f"  • {factor}")
            text.append("")
        
        # Negative factors
        negative = reasons.get('negative_factors', [])
        if negative:
            text.append("✗ 負面因素")
            text.append("-" * 40)
            for factor in negative:
                text.append(f"  • {factor}")
            text.append("")
        
        # Key statistics
        stats = reasons.get('key_statistics', [])
        if stats:
            text.append("關鍵統計")
            text.append("-" * 40)
            for stat in stats:
                text.append(f"  • {stat}")
            text.append("")
        
        # Prediction summary
        summary = reasons.get('prediction_summary', '')
        if summary:
            text.append("預測摘要")
            text.append("-" * 40)
            text.append(f"  {summary}")
            text.append("")
        
        # Form score
        form_score = pred.get('form_score', 0)
        if form_score > 0:
            text.append("形勢分析")
            text.append("-" * 40)
            text.append(f"形勢評分: {form_score:.0f}%")
            text.append("")
        
        # Interaction multiplier
        interaction = pred.get('interaction_multiplier', 1)
        if interaction != 1:
            text.append("因素互動")
            text.append("-" * 40)
            text.append(f"綜合倍數: {interaction:.2f}x")
            text.append("")
        
        self.reasons_content.setText('\n'.join(text))
    
    def update_race_info(self):
        """Update race information in the analysis tab."""
        info = self.race_info
        
        # Update labels
        for child in self.findChildren(QLabel):
            obj_name = child.objectName()
            if obj_name in info:
                child.setText(str(info[obj_name]))
        
        # Update field size
        field_size = info.get('field_size', len(self.predictions))
        for child in self.findChildren(QLabel):
            if child.objectName() == 'field_size':
                child.setText(str(field_size))
        
        # Update model info
        if hasattr(self, 'result'):
            model_info = self.result.get('analysis', '')
            if model_info:
                self.model_info.setText(f"模型: 增強版 v2.0\n校準: 冪律\n特徵: 100+\n\n{model_info}")


import os
