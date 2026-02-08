"""
賽事預測詳情彈窗 - 顯示選定賽事的預測和排名
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QScrollArea, QFrame, QPushButton, QTabWidget, QWidget, QTextEdit
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor
import sqlite3
from datetime import datetime


class LiveOddsRefreshWorker(QThread):
    """背景工作進程用於刷新即時賠率"""
    refresh_complete = pyqtSignal(int)
    error = pyqtSignal(str)
    
    def __init__(self, race_date: str, race_number: int, racecourse: str):
        super().__init__()
        self.race_date = race_date
        self.race_number = race_number
        self.racecourse = racecourse
        
    def run(self):
        """抓取並保存最新賠率"""
        try:
            import sys
            import os
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sys.path.insert(0, parent_dir)
            
            from scraper.pipeline import HKJCDataPipeline
            
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'hkjc_races.db')
            pipeline = HKJCDataPipeline(db_path)
            
            # 標準化日期
            normalized_date = self.race_date
            if ' ' in str(self.race_date):
                normalized_date = str(self.race_date).split(' ')[0]
                
            count = pipeline.save_live_odds(normalized_date, self.race_number, self.racecourse)
            self.refresh_complete.emit(count)
        except Exception as e:
            self.error.emit(str(e))


class PredictionLoaderWorker(QThread):
    """背景工作進程用於加載預測"""
    predictions_loaded = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, race_date: str, race_number: int):
        super().__init__()
        self.race_date = race_date
        self.race_number = race_number
    
    def run(self):
        """加載預測和實際結果"""
        try:
            import sys
            import os
            
            # 修復導入路徑以匹配您的項目結構
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sys.path.insert(0, parent_dir)
            
            from engine.prediction.enhanced_predictor import EnhancedRacePredictor
            
            # 使用您的實際數據庫路徑
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'hkjc_races.db')
            
            if not os.path.exists(db_path):
                self.error.emit(f"數據庫未找到: {db_path}")
                return
            
            predictor = EnhancedRacePredictor(db_path)
            
            # 標準化日期
            normalized_date = self.race_date
            if ' ' in str(self.race_date):
                normalized_date = str(self.race_date).split(' ')[0]
            
            # 獲取賽道信息
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Try future_race_cards, then fixtures, then race_results
            racecourse = None
            
            # 1. future_race_cards
            cursor.execute("""
                SELECT DISTINCT racecourse FROM future_race_cards
                WHERE race_date LIKE ? AND race_number = ?
                LIMIT 1
            """, (f"{normalized_date}%", self.race_number))
            row = cursor.fetchone()
            if row:
                racecourse = row['racecourse']
            
            # 2. fixtures
            if not racecourse:
                cursor.execute("""
                    SELECT racecourse FROM fixtures
                    WHERE race_date LIKE ? AND race_number = ?
                    LIMIT 1
                """, (f"{normalized_date}%", self.race_number))
                row = cursor.fetchone()
                if row:
                    racecourse = row['racecourse']
            
            # 3. race_results
            if not racecourse:
                cursor.execute("""
                    SELECT racecourse FROM race_results
                    WHERE race_date LIKE ? AND race_number = ?
                    LIMIT 1
                """, (f"{normalized_date}%", self.race_number))
                row = cursor.fetchone()
                if row:
                    racecourse = row['racecourse']
            
            if not racecourse:
                # Default to ST if not found
                racecourse = 'ST'
            
            # 生成預測
            predictions = predictor.predict_race(normalized_date, self.race_number, racecourse)
            
            # 獲取實際結果用於比較（按馬名匹配）
            cursor.execute("""
                SELECT horse_name, position FROM race_results
                WHERE race_date = ? AND race_number = ? AND racecourse = ?
                ORDER BY position
            """, (normalized_date, self.race_number, racecourse))
            
            results_rows = cursor.fetchall()
            actual_results = {row['horse_name']: row['position'] for row in results_rows}
            has_history = len(actual_results) > 0
            
            conn.close()
            
            result_data = {
                'race_date': normalized_date,
                'race_number': self.race_number,
                'racecourse': racecourse,
                'predictions': predictions,
                'actual_results': actual_results,
                'has_history': has_history
            }
            
            self.predictions_loaded.emit(result_data)
            
        except Exception as e:
            import traceback
            error_msg = f"加載預測失敗: {str(e)}\n{traceback.format_exc()}"
            self.error.emit(error_msg)


class RacePredictionModal(QDialog):
    """顯示賽事預測和排名的彈窗"""
    
    def __init__(self, race_date: str, race_number: int, parent=None):
        super().__init__(parent)
        self.race_date = race_date
        self.race_number = race_number
        self.has_history = False
        self.setWindowTitle(f"賽事 {race_number} - {race_date}")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet("background-color: #0f172a;")
        
        self.init_ui()
        self.load_predictions()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # 標題
        header_layout = QHBoxLayout()
        title = QLabel(f"賽事 {self.race_number} - {self.race_date}")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #f8fafc;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # 刷新按鈕
        self.refresh_btn = QPushButton(self.tr("刷新賠率"))
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #cbd5e1;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #334155;
                border-color: #475569;
            }
        """)
        self.refresh_btn.clicked.connect(self.refresh_live_odds)
        header_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(header_layout)
        
        # 信息標籤
        self.info_label = QLabel(self.tr("正在加載預測..."))
        self.info_label.setStyleSheet("color: #cbd5e1; font-size: 11px;")
        layout.addWidget(self.info_label)
        
        # 標籤頁
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #334155; }
            QTabBar::tab { 
                background-color: #1e293b; 
                color: #cbd5e1; 
                padding: 8px 16px;
                border: 1px solid #334155;
            }
            QTabBar::tab:selected { 
                background-color: #334155; 
                color: #f8fafc;
            }
        """)
        layout.addWidget(self.tabs)
        
        # 推理部件（用於未來賽事）
        self.reasoning_widget = QWidget()
        reasoning_layout = QVBoxLayout(self.reasoning_widget)
        self.reasoning_text = QTextEdit()
        self.reasoning_text.setReadOnly(True)
        self.reasoning_text.setStyleSheet("""
            QTextEdit {
                background-color: #0f172a;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 12px;
                font-family: 'Courier New';
                font-size: 10px;
            }
        """)
        reasoning_layout.addWidget(self.reasoning_text)
        
        # 關閉按鈕
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        close_btn = QPushButton(self.tr("關閉"))
        close_btn.setStyleSheet("""
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
        """)
        close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(close_btn)
        layout.addLayout(footer_layout)
    
    def load_predictions(self):
        """在背景中加載預測"""
        self.worker = PredictionLoaderWorker(self.race_date, self.race_number)
        self.worker.predictions_loaded.connect(self._on_predictions_loaded)
        self.worker.error.connect(self._on_error)
        self.worker.start()
    
    def refresh_live_odds(self):
        """Trigger live odds refresh using Selenium"""
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText(self.tr("正在抓取..."))
        self.info_label.setText(self.tr("正在使用 Selenium 抓取最新賠率..."))
        
        # We need racecourse for the worker
        # If we don't have it yet, we'll try to find it from the database first
        racecourse = getattr(self, 'racecourse', 'ST')
        
        self.refresh_worker = LiveOddsRefreshWorker(self.race_date, self.race_number, racecourse)
        self.refresh_worker.refresh_complete.connect(self._on_refresh_complete)
        self.refresh_worker.error.connect(self._on_error)
        self.refresh_worker.start()
        
    def _on_refresh_complete(self, count):
        """Called when odds refresh is complete"""
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText(self.tr("刷新賠率"))
        self.info_label.setText(self.tr("賠率更新成功（{} 條記錄）。正在重新計算預測...").format(count))
        # Reload predictions with new odds
        self.load_predictions()

    def _on_error(self, message):
        """處理錯誤"""
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText(self.tr("刷新賠率"))
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(self, self.tr("錯誤"), message)

    def _on_predictions_loaded(self, result_data: dict):
        """處理預測已加載"""
        if 'error' in result_data:
            self._on_error(result_data['error'])
            return
        
        self.racecourse = result_data.get('racecourse', 'ST')
        self.has_history = result_data.get('has_history', False)
        predictions = result_data.get('predictions', {})
        actual_results = result_data.get('actual_results', {})
        
        self.info_label.setText(f"賽事 {result_data['race_number']} • {result_data['racecourse']}")
        self.info_label.setStyleSheet("color: #cbd5e1; font-size: 11px;")
        
        pred_list = predictions.get('predictions', [])
        
        if self.has_history:
            self._setup_comparison_view(pred_list, actual_results)
        else:
            self._setup_prediction_reasoning_view(pred_list)
    
    def _setup_prediction_reasoning_view(self, pred_list):
        """顯示未來賽事的詳細預測推理"""
        self.tabs.clear()
        
        # 標籤頁1: 預測表格
        predictions_table = QTableWidget()
        predictions_table.setColumnCount(6)
        predictions_table.setHorizontalHeaderLabels([self.tr("排名"), self.tr("馬名"), self.tr("勝率%"), self.tr("信心%"), self.tr("值博%"), self.tr("賠率")])
        predictions_table.setRowCount(len(pred_list))
        predictions_table.setStyleSheet("""
            QTableWidget {
                background-color: #0f172a;
                border: 1px solid #334155;
                gridline-color: #334155;
            }
            QTableWidget::item {
                padding: 8px;
                color: #f8fafc;
            }
            QHeaderView::section {
                background-color: #1e293b;
                color: #f8fafc;
                padding: 8px;
                font-weight: 600;
            }
        """)
        
        for row_idx, pred in enumerate(pred_list):
            # 排名
            rank = QTableWidgetItem(str(row_idx + 1))
            rank.setForeground(QColor("#cbd5e1"))
            predictions_table.setItem(row_idx, 0, rank)
            
            # 馬名
            horse_name = QTableWidgetItem(pred.get('horse_name', ''))
            horse_name.setForeground(QColor("#f8fafc"))
            predictions_table.setItem(row_idx, 1, horse_name)
            
            # 勝率
            win_prob = pred.get('win_probability', 0)
            win_prob_item = QTableWidgetItem(f"{win_prob:.1f}%")
            win_prob_item.setForeground(QColor("#10b981") if win_prob > 15 else QColor("#94a3b8"))
            predictions_table.setItem(row_idx, 2, win_prob_item)
            
            # 信心
            confidence = pred.get('confidence', 0) * 100
            confidence_item = QTableWidgetItem(f"{confidence:.1f}%")
            confidence_item.setForeground(QColor("#3b82f6"))
            predictions_table.setItem(row_idx, 3, confidence_item)
            
            # 值博
            value_pct = pred.get('value_pct', None)
            if value_pct is not None:
                value_item = QTableWidgetItem(f"{value_pct:+.0f}%")
                if value_pct > 10:
                    value_item.setForeground(QColor("#10b981"))  # 好值博
                elif value_pct < -10:
                    value_item.setForeground(QColor("#ef4444"))  # 差值博
                else:
                    value_item.setForeground(QColor("#94a3b8"))  # 中性
            else:
                value_item = QTableWidgetItem(self.tr("N/A"))
                value_item.setForeground(QColor("#6b7280"))  # 灰色
            predictions_table.setItem(row_idx, 4, value_item)
            
            # 賠率
            odds = pred.get('current_odds', None)
            if odds is not None and odds > 0:
                odds_item = QTableWidgetItem(f"{odds:.1f}")
            else:
                odds_item = QTableWidgetItem(self.tr("N/A"))
            odds_item.setForeground(QColor("#cbd5e1"))
            predictions_table.setItem(row_idx, 5, odds_item)
        
        predictions_table.resizeColumnsToContents()
        self.tabs.addTab(predictions_table, self.tr("預測"))

        # 標籤頁2: 詳細推理
        self._build_reasoning_text(pred_list)
        self.tabs.addTab(self.reasoning_widget, self.tr("預測推理"))
    
    def _setup_comparison_view(self, pred_list, actual_results):
        """顯示有結果賽事的比較"""
        self.tabs.clear()
        
        # 標籤頁1: 比較表格
        comparison_table = QTableWidget()
        comparison_table.setColumnCount(7)
        comparison_table.setHorizontalHeaderLabels([self.tr("預測排名"), self.tr("馬名"), self.tr("勝率%"), self.tr("信心%"), self.tr("實際名次"), self.tr("名次差"), self.tr("準確度")])
        comparison_table.setRowCount(len(pred_list))
        comparison_table.setStyleSheet("""
            QTableWidget {
                background-color: #0f172a;
                border: 1px solid #334155;
                gridline-color: #334155;
            }
            QTableWidget::item {
                padding: 8px;
                color: #f8fafc;
            }
            QHeaderView::section {
                background-color: #1e293b;
                color: #f8fafc;
                padding: 8px;
                font-weight: 600;
            }
        """)
        
        for row_idx, pred in enumerate(pred_list):
            pred_rank = row_idx + 1
            horse_name = pred.get('horse_name', '')
            actual_pos = actual_results.get(horse_name)
            pos_diff = (pred_rank - actual_pos) if actual_pos else None
            
            # 預測排名
            rank_item = QTableWidgetItem(str(pred_rank))
            rank_item.setForeground(QColor("#cbd5e1"))
            comparison_table.setItem(row_idx, 0, rank_item)
            
            # 馬名
            horse_item = QTableWidgetItem(horse_name)
            horse_item.setForeground(QColor("#f8fafc"))
            comparison_table.setItem(row_idx, 1, horse_item)
            
            # 勝率
            win_prob = pred.get('win_probability', 0)
            win_prob_item = QTableWidgetItem(f"{win_prob:.1f}%")
            win_prob_item.setForeground(QColor("#10b981") if win_prob > 15 else QColor("#94a3b8"))
            comparison_table.setItem(row_idx, 2, win_prob_item)
            
            # 信心
            confidence = pred.get('confidence', 0) * 100
            confidence_item = QTableWidgetItem(f"{confidence:.1f}%")
            confidence_item.setForeground(QColor("#3b82f6"))
            comparison_table.setItem(row_idx, 3, confidence_item)
            
            # 實際名次
            if actual_pos:
                actual_item = QTableWidgetItem(self.tr("名次 {}").format(actual_pos))
                if actual_pos == 1:
                    actual_item.setForeground(QColor("#10b981"))  # 冠軍
                elif actual_pos <= 3:
                    actual_item.setForeground(QColor("#f59e0b"))  # 前三名
                else:
                    actual_item.setForeground(QColor("#94a3b8"))  # 其他
            else:
                actual_item = QTableWidgetItem(self.tr("未完成"))
                actual_item.setForeground(QColor("#ef4444"))
            comparison_table.setItem(row_idx, 4, actual_item)
            
            # 名次差
            if pos_diff is not None:
                diff_item = QTableWidgetItem(f"{pos_diff:+d}")
                if abs(pos_diff) == 0:
                    diff_item.setForeground(QColor("#10b981"))  # 完美
                elif abs(pos_diff) <= 2:
                    diff_item.setForeground(QColor("#f59e0b"))  # 接近
                else:
                    diff_item.setForeground(QColor("#ef4444"))  # 偏差大
            else:
                diff_item = QTableWidgetItem(self.tr("N/A"))
                diff_item.setForeground(QColor("#6b7280"))
            comparison_table.setItem(row_idx, 5, diff_item)
            
            # 準確度
            accuracy_key = self._get_accuracy_label(pos_diff)
            accuracy_item = QTableWidgetItem(self.tr(accuracy_key))
            if accuracy_key == "完美":
                accuracy_item.setForeground(QColor("#10b981"))
            elif accuracy_key == "良好":
                accuracy_item.setForeground(QColor("#f59e0b"))
            elif accuracy_key == "差":
                accuracy_item.setForeground(QColor("#ef4444"))
            else:
                accuracy_item.setForeground(QColor("#6b7280"))
            comparison_table.setItem(row_idx, 6, accuracy_item)
        
        comparison_table.resizeColumnsToContents()
        self.tabs.addTab(comparison_table, self.tr("比較"))
        
        # 標籤頁2: 準確度總結
        accuracy_stats = self._calculate_accuracy_stats(pred_list, actual_results)
        self._setup_accuracy_summary_tab(accuracy_stats)
    
    def _build_reasoning_text(self, pred_list):
        """為預測建立詳細的推理文本"""
        reasoning = ""
        
        for idx, pred in enumerate(pred_list[:5], 1):  # 前5名馬匹
            reasoning += f"\n{'='*80}\n"
            reasoning += f"{self.tr('排名')} {idx}: {pred.get('horse_name', '未知').upper()}\n"
            reasoning += f"{'='*80}\n\n"
            
            # 基本預測信息
            reasoning += f"{self.tr('勝率')}: {pred.get('win_probability', 0):.1f}%\n"
            reasoning += f"{self.tr('信心評分')}: {pred.get('confidence', 0)*100:.1f}%\n"
            reasoning += f"{self.tr('風險評分')}: {pred.get('risk_score', 0):.1f}/100\n"
            value_pct = pred.get('value_pct', None)
            if value_pct is not None:
                reasoning += f"{self.tr('值博')}: {value_pct:+.0f}%\n"
            else:
                reasoning += f"{self.tr('值博')}: {self.tr('N/A')}\n"
            reasoning += "\n"
            
            # 數學解釋
            math_exp = pred.get('mathematical_explanation', {})
            reasoning += f"{self.tr('數學分析')}:\n"
            reasoning += f"  • {self.tr('原始概率')}: {math_exp.get('raw_probability', 0)*100:.1f}%\n"
            reasoning += f"  • {self.tr('校準概率')}: {math_exp.get('calibrated_prob', 0)*100:.1f}%\n"
            reasoning += f"  • {self.tr('校準調整')}: {math_exp.get('calibration_reduction', 0):.1f}%\n"
            reasoning += f"  • {self.tr('交互乘數')}: {math_exp.get('interaction_multiplier', 1):.2f}x\n\n"
            
            # 基礎因素
            base_factors = math_exp.get('base_factors', {})
            if base_factors:
                reasoning += f"{self.tr('基礎因素貢獻')}:\n"
                for factor, value in base_factors.items():
                    reasoning += f"  • {factor.replace('_', ' ').title()}: {value*100:+.1f}%\n"
                reasoning += "\n"
            
            # 馬匹詳細信息
            reasoning += f"{self.tr('馬匹詳細信息')}:\n"
            reasoning += f"  • {self.tr('騎師')}: {pred.get('jockey', self.tr('N/A'))}\n"
            reasoning += f"  • {self.tr('練馬師')}: {pred.get('trainer', self.tr('N/A'))}\n"
            reasoning += f"  • {self.tr('負磅')}: {pred.get('weight', self.tr('N/A'))}\n"
            reasoning += f"  • {self.tr('閘位')}: {pred.get('draw', self.tr('N/A'))}\n"
            odds = pred.get('current_odds', None)
            if odds is not None and odds > 0:
                reasoning += f"  • {self.tr('當前賠率')}: {odds:.1f}\n"
            else:
                reasoning += f"  • {self.tr('當前賠率')}: {self.tr('N/A')}\n"
            reasoning += "\n"
            
            # 風險評估
            reasoning += f"{self.tr('風險評估')}: {pred.get('risk_recommendation', '評估')}\n"
            reasoning += f"{self.tr('總體風險評分')}: {pred.get('risk_score', 0):.1f}/100\n\n"
        
        self.reasoning_text.setText(reasoning)
    
    def _calculate_accuracy_stats(self, pred_list, actual_results):
        """計算預測準確度統計"""
        stats = {
            'total_horses': len(pred_list),
            'perfect_predictions': 0,
            'good_predictions': 0,
            'winner_correct': False,
            'top3_correct': 0,
            'avg_position_diff': 0,
            'position_diffs': []
        }
        
        for idx, pred in enumerate(pred_list):
            pred_rank = idx + 1
            horse_name = pred.get('horse_name', '')
            actual_pos = actual_results.get(horse_name)
            
            if actual_pos:
                pos_diff = pred_rank - actual_pos
                stats['position_diffs'].append(pos_diff)
                
                if abs(pos_diff) == 0:
                    stats['perfect_predictions'] += 1
                elif abs(pos_diff) <= 2:
                    stats['good_predictions'] += 1
                
                if pred_rank == 1 and actual_pos == 1:
                    stats['winner_correct'] = True
                
                if pred_rank <= 3 and actual_pos <= 3:
                    stats['top3_correct'] += 1
        
        if stats['position_diffs']:
            stats['avg_position_diff'] = sum(abs(d) for d in stats['position_diffs']) / len(stats['position_diffs'])
        
        return stats
    
    def _get_accuracy_label(self, pos_diff):
        """根據名次差獲取準確度標籤"""
        if pos_diff is None:
            return self.tr("N/A")
        diff = abs(pos_diff)
        if diff == 0:
            return self.tr("完美")
        elif diff <= 2:
            return self.tr("良好")
        else:
            return self.tr("差")
    
    def _setup_accuracy_summary_tab(self, accuracy_stats):
        """創建準確度總結標籤頁，包含詳細統計"""
        summary_widget = QWidget()
        layout = QVBoxLayout(summary_widget)
        
        total_horses = accuracy_stats['total_horses']
        perfect_pct = (accuracy_stats['perfect_predictions'] / total_horses * 100) if total_horses > 0 else 0.0
        good_pct = (accuracy_stats['good_predictions'] / total_horses * 100) if total_horses > 0 else 0.0
        
        stats_text = self.tr("""
        預測準確度總結
        {sep}

        總馬匹數: {total}
        完美預測（準確名次）: {perfect} ({perfect_pct}%)
        良好預測（相差2名以內）: {good} ({good_pct}%)
        冠軍預測正確: {winner}
        前三名準確度: {top3}/3 ({top3_pct}%)
        平均名次差: {avg} 名

        準確度分類:
        • 完美: 完全預測到最終名次
        • 良好: 預測名次與實際相差2名以內
        • 差: 預測名次與實際相差3名或以上
        """).format(
            sep='='*50,
            total=total_horses,
            perfect=accuracy_stats['perfect_predictions'],
            perfect_pct=f"{perfect_pct:.1f}",
            good=accuracy_stats['good_predictions'],
            good_pct=f"{good_pct:.1f}",
            winner=self.tr('是') if accuracy_stats['winner_correct'] else self.tr('否'),
            top3=accuracy_stats['top3_correct'],
            top3_pct=f"{accuracy_stats['top3_correct']/3*100:.1f}" if accuracy_stats['top3_correct'] > 0 else "0.0",
            avg=f"{accuracy_stats['avg_position_diff']:.2f}"
        )
        
        stats_label = QLabel(stats_text)
        stats_label.setStyleSheet("""
            QLabel {
                color: #f8fafc;
                font-family: 'Courier New';
                font-size: 12px;
                background-color: #0f172a;
                padding: 20px;
                border-radius: 8px;
                border: 1px solid #334155;
            }
        """)
        stats_label.setWordWrap(True)
        layout.addWidget(stats_label)
        
        self.tabs.addTab(summary_widget, self.tr("準確度統計"))
    
    def _on_error(self, error_msg: str):
        """處理加載預測時的錯誤"""
        self.info_label.setText(f"錯誤: {error_msg}")
        self.info_label.setStyleSheet("color: #ef4444; font-size: 11px;")
        self.tabs.clear()