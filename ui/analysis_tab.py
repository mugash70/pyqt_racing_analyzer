#!/usr/bin/env python3
"""
Analysis Tab - Race statistics and patterns
"""

import sqlite3
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QTableWidget,
    QTableWidgetItem, QComboBox, QSpinBox, QPushButton, QProgressBar,
    QSplitter, QTextEdit, QCheckBox, QTabWidget
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor
import pandas as pd


class AnalysisTab(QWidget):
    """Analysis and statistics tab"""
    
    def __init__(self, db_path: str = None, parent=None):
        super().__init__(parent)
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'hkjc_races.db')
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI with tabs for different analysis types"""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # self.header = QLabel(self.tr("Race Analysis & Statistics"))
        # self.header.setFont(QFont("Arial", 20, QFont.Bold))
        # self.header.setStyleSheet("color: #f8fafc;")
        # layout.addWidget(self.header)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(self._tab_style())
        
        # Create tabs for each analysis type
        self._create_analysis_tabs()
        
        layout.addWidget(self.tab_widget, 1)
        
        self.setLayout(layout)
        
        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        # Load initial analysis
        self.on_tab_changed(0)

    def _create_analysis_tabs(self):
        """Create tabs for different analysis types based on available data"""
        cursor = self.conn.cursor()
        
        # Get table info to check what columns exist
        cursor.execute("PRAGMA table_info(race_results)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Check what data is available
        cursor.execute("SELECT COUNT(*) FROM race_results")
        has_race_results = cursor.fetchone()[0] > 0
        
        cursor.execute("SELECT COUNT(*) FROM barrier_draws")
        has_barrier_data = cursor.fetchone()[0] > 0
        
        cursor.execute("SELECT COUNT(*) FROM race_results WHERE horse_name IS NOT NULL AND horse_name != ''")
        has_horse_data = cursor.fetchone()[0] > 0
        
        # Only check weight if column exists
        has_weight_data = False
        if 'weight' in columns:
            cursor.execute("SELECT COUNT(*) FROM race_results WHERE weight IS NOT NULL AND weight != '' AND weight != '0'")
            has_weight_data = cursor.fetchone()[0] > 0
        
        # Only check distance if column exists
        has_distance_data = False
        if 'race_distance' in columns:
            cursor.execute("SELECT COUNT(*) FROM race_results WHERE race_distance IS NOT NULL AND race_distance != ''")
            has_distance_data = cursor.fetchone()[0] > 0
        
        analysis_types = []
        
        if has_race_results:
            analysis_types.append(("整體統計", self._create_overall_tab))
            analysis_types.append(("騎師表現", self._create_jockey_tab))
            analysis_types.append(("練馬師分析", self._create_trainer_tab))
        
        if has_barrier_data:
            analysis_types.append(("閘位分析", self._create_barrier_tab))
        
        if has_horse_data:
            analysis_types.append(("馬匹表現", self._create_horse_tab))
        
        if has_weight_data:
            analysis_types.append(("負重分析", self._create_weight_tab))
        
        if has_distance_data:
            analysis_types.append(("距離分析", self._create_distance_tab))
        
        # Comment out specialized tabs to hide them
        # try:
        #     from .specialized_tabs import RaceReportsTab, ExerciseDataTab, ProfessionalSchedulesTab
        #     analysis_types.append(("賽事報告", lambda: RaceReportsTab(self.db_path)))
        #     analysis_types.append(("晨操數據", lambda: ExerciseDataTab(self.db_path)))
        #     analysis_types.append(("專業日程", lambda: ProfessionalSchedulesTab(self.db_path)))
        # except ImportError:
        #     pass

        for tab_name, create_func in analysis_types:
            tab_widget = create_func()
            self.tab_widget.addTab(tab_widget, self.tr(tab_name))
    
    def _create_overall_tab(self):
        """Create overall statistics tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        table = QTableWidget()
        table.setStyleSheet(self._table_style())
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["類別", "數值", "百分比", "單位"])
        
        layout.addWidget(table)
        widget.table = table  # Store reference
        return widget
    
    def _create_barrier_tab(self):
        """Create barrier analysis tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        table = QTableWidget()
        table.setStyleSheet(self._table_style())
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["閘位", "出賽次數", "勝出次數", "勝率"])
        
        layout.addWidget(table)
        widget.table = table
        return widget
    
    def _create_jockey_tab(self):
        """Create jockey performance tab with chart"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # Left side - table
        table = QTableWidget()
        table.setStyleSheet(self._table_style())
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["騎師", "出賽次數", "勝出次數", "勝率"])
        
        # Right side - simple chart area
        chart_area = QWidget()
        chart_area.setStyleSheet("background-color: #1e293b; border: 1px solid #334155; border-radius: 8px;")
        chart_area.setMinimumSize(300, 200)
        
        chart_layout = QVBoxLayout(chart_area)
        chart_title = QLabel("頂尖騎師勝率")
        chart_title.setStyleSheet("color: #f8fafc; font-weight: bold; padding: 10px;")
        chart_layout.addWidget(chart_title)
        
        self.jockey_chart = QLabel("圖表將顯示於此")
        self.jockey_chart.setStyleSheet("color: #cbd5e1; padding: 20px;")
        self.jockey_chart.setAlignment(Qt.AlignCenter)
        chart_layout.addWidget(self.jockey_chart)
        
        layout.addWidget(table, 2)
        layout.addWidget(chart_area, 1)
        
        widget.table = table
        widget.chart = self.jockey_chart
        return widget
    
    def _create_trainer_tab(self):
        """Create trainer analysis tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        table = QTableWidget()
        table.setStyleSheet(self._table_style())
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["練馬師", "出賽次數", "勝出次數", "勝率"])
        
        layout.addWidget(table)
        widget.table = table
        return widget
    
    def _create_horse_tab(self):
        """Create horse performance tab with dropdown and charts"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Controls
        controls = QFrame()
        controls.setStyleSheet("background-color: #1e293b; border-radius: 8px; padding: 12px;")
        controls_layout = QHBoxLayout(controls)
        
        controls_layout.addWidget(QLabel("選擇馬匹:"))
        horse_combo = QComboBox()
        horse_combo.setStyleSheet(self._combo_style())
        horse_combo.currentTextChanged.connect(self._on_horse_selected)
        controls_layout.addWidget(horse_combo)
        controls_layout.addStretch()
        
        layout.addWidget(controls)
        
        # Split layout for table and chart
        content_layout = QHBoxLayout()
        
        # Left side - table
        table = QTableWidget()
        table.setStyleSheet(self._table_style())
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["賽事日期", "賽事", "名次", "總馬匹數", "表現"])
        
        # Right side - rank chart
        chart_area = QWidget()
        chart_area.setStyleSheet("background-color: #1e293b; border: 1px solid #334155; border-radius: 8px;")
        chart_area.setMinimumSize(300, 250)
        
        chart_layout = QVBoxLayout(chart_area)
        chart_title = QLabel("最終名次趨勢")
        chart_title.setStyleSheet("color: #f8fafc; font-weight: bold; padding: 10px;")
        chart_layout.addWidget(chart_title)
        
        self.horse_chart = QLabel("請選擇馬匹以查看名次圖表")
        self.horse_chart.setStyleSheet("color: #cbd5e1; padding: 20px; font-family: monospace;")
        self.horse_chart.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        chart_layout.addWidget(self.horse_chart)
        
        content_layout.addWidget(table, 2)
        content_layout.addWidget(chart_area, 1)
        
        layout.addLayout(content_layout)
        
        widget.table = table
        widget.horse_combo = horse_combo
        widget.chart = self.horse_chart
        return widget
    
    def _create_weight_tab(self):
        """Create weight analysis tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        table = QTableWidget()
        table.setStyleSheet(self._table_style())
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["負重範圍", "出賽次數", "勝出次數", "勝率"])
        
        layout.addWidget(table)
        widget.table = table
        return widget
    
    def _create_distance_tab(self):
        """Create distance analysis tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        table = QTableWidget()
        table.setStyleSheet(self._table_style())
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["距離", "出賽次數", "勝出次數", "勝率"])
        
        layout.addWidget(table)
        widget.table = table
        return widget
    
    def on_tab_changed(self, index):
        """Handle tab change"""
        if index >= 0 and index < self.tab_widget.count():
            tab_text = self.tab_widget.tabText(index)
            if "整體" in tab_text:
                self._load_overall_stats()
            elif "閘位" in tab_text:
                self._load_barrier_analysis()
            elif "騎師" in tab_text:
                self._load_jockey_analysis()
            elif "練馬師" in tab_text:
                self._load_trainer_analysis()
            elif "馬匹" in tab_text:
                self._load_horse_analysis()
            elif "負重" in tab_text:
                self._load_weight_analysis()
            elif "距離" in tab_text:
                self._load_distance_analysis()
    
    def _load_overall_stats(self):
        """Show overall dataset statistics"""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(DISTINCT race_date || '-' || race_number) FROM race_results")
        total_races = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(DISTINCT horse_name) FROM race_results")
        total_horses = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM race_results WHERE position = 1")
        total_winners = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM race_results")
        total_starts = cursor.fetchone()[0] or 0
        
        # Get current tab's table
        current_widget = self.tab_widget.currentWidget()
        if not hasattr(current_widget, 'table'):
            return
            
        table = current_widget.table
        table.setRowCount(4)
        
        data = [
            ("總歷史賽事", total_races, "", "場賽事"),
            ("獨特馬匹", total_horses, "", "匹馬"),
            ("總出賽次數", total_starts, "", "次出賽"),
            ("總勝出次數", total_winners, f"{(total_winners/total_starts*100):.1f}%" if total_starts > 0 else "0%", "場勝出"),
        ]
        
        for row_idx, (cat, val, pct, unit) in enumerate(data):
            table.setItem(row_idx, 0, QTableWidgetItem(cat))
            table.setItem(row_idx, 1, QTableWidgetItem(str(val)))
            table.setItem(row_idx, 2, QTableWidgetItem(pct))
            table.setItem(row_idx, 3, QTableWidgetItem(unit))
    
    def _load_barrier_analysis(self):
        """Analyze barrier position performance"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                barrier_position as category,
                COUNT(*) as total,
                SUM(CASE WHEN wins > 0 THEN 1 ELSE 0 END) as wins,
                ROUND(SUM(CASE WHEN wins > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as win_rate
            FROM barrier_draws
            WHERE barrier_position BETWEEN 1 AND 14
            GROUP BY barrier_position
            ORDER BY barrier_position
        """)
        
        self._display_tab_results(cursor.fetchall())
    
    def _load_jockey_analysis(self):
        """Analyze jockey performance"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                jockey as category,
                COUNT(*) as total,
                SUM(CASE WHEN position = 1 THEN 1 ELSE 0 END) as wins,
                ROUND(SUM(CASE WHEN position = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as win_rate
            FROM race_results
            WHERE jockey IS NOT NULL AND jockey != ''
            GROUP BY jockey
            HAVING COUNT(*) >= 5
            ORDER BY win_rate DESC
            LIMIT 20
        """)
        
        results = cursor.fetchall()
        self._display_tab_results(results)
        
        # Update chart if it exists
        current_widget = self.tab_widget.currentWidget()
        if hasattr(current_widget, 'chart') and results:
            chart_text = "頭5位騎師:\n\n"
            for i, row in enumerate(results[:5]):
                chart_text += f"{i+1}. {row[0]}: {row[3]:.1f}%\n"
            current_widget.chart.setText(chart_text)
    
    def _load_trainer_analysis(self):
        """Analyze trainer performance"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                trainer as category,
                COUNT(*) as total,
                SUM(CASE WHEN position = 1 THEN 1 ELSE 0 END) as wins,
                ROUND(SUM(CASE WHEN position = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as win_rate
            FROM race_results
            WHERE trainer IS NOT NULL AND trainer != ''
            GROUP BY trainer
            HAVING COUNT(*) >= 5
            ORDER BY win_rate DESC
            LIMIT 20
        """)
        
        self._display_tab_results(cursor.fetchall())
    
    def _load_horse_analysis(self):
        """Load horse dropdown and initial data"""
        cursor = self.conn.cursor()
        
        # Get all horses with race data
        cursor.execute("""
            SELECT DISTINCT horse_name
            FROM race_results
            WHERE horse_name IS NOT NULL AND horse_name != ''
            ORDER BY horse_name
        """)
        
        horses = [row[0] for row in cursor.fetchall()]
        
        current_widget = self.tab_widget.currentWidget()
        if hasattr(current_widget, 'horse_combo'):
            current_widget.horse_combo.clear()
            current_widget.horse_combo.addItems(horses)
            
            # Load data for first horse if available
            if horses:
                self._load_horse_performance(horses[0])
    
    def _on_horse_selected(self, horse_name):
        """Handle horse selection from dropdown"""
        if horse_name:
            self._load_horse_performance(horse_name)
    
    def _load_horse_performance(self, horse_name):
        """Load performance data for selected horse with rank chart"""
        cursor = self.conn.cursor()
        
        # Get last 10 races for the horse
        cursor.execute("""
            SELECT race_date, race_number, position, 
                   (SELECT COUNT(*) FROM race_results r2 
                    WHERE r2.race_date = r1.race_date AND r2.race_number = r1.race_number) as total_horses
            FROM race_results r1
            WHERE horse_name = ? AND position IS NOT NULL AND position != '' AND position != '0'
            ORDER BY race_date DESC, race_number DESC
            LIMIT 10
        """, (horse_name,))
        
        races = cursor.fetchall()
        
        current_widget = self.tab_widget.currentWidget()
        if not hasattr(current_widget, 'table'):
            return
            
        table = current_widget.table
        table.setRowCount(min(5, len(races)))
        
        # Fill table with last 5 races
        positions = []
        for row_idx, race in enumerate(races[:5]):
            table.setItem(row_idx, 0, QTableWidgetItem(str(race[0])))
            table.setItem(row_idx, 1, QTableWidgetItem(f"第{race[1]}場"))
            table.setItem(row_idx, 2, QTableWidgetItem(str(race[2])))
            table.setItem(row_idx, 3, QTableWidgetItem(str(race[3])))
            
            # Performance indicator
            pos = int(race[2])
            total = int(race[3])
            perf = "第1名" if pos == 1 else "第2名" if pos == 2 else "第3名" if pos == 3 else f"第{pos}名"
            table.setItem(row_idx, 4, QTableWidgetItem(f"{perf} 共{total}匹"))
            
            positions.append(pos)
        
        # Create rank chart for all available races (up to 10)
        all_positions = [int(race[2]) for race in races]
        self._create_rank_chart(all_positions, horse_name)
    
    def _create_rank_chart(self, positions, horse_name):
        """Create ASCII rank chart showing finishing positions"""
        if not positions:
            return
        
        current_widget = self.tab_widget.currentWidget()
        if not hasattr(current_widget, 'chart'):
            return
        
        chart_text = f"最近{len(positions)}場比賽名次\n\n"
        
        # Find max position for scaling
        max_pos = max(positions)
        
        # Create horizontal bar chart
        for i, pos in enumerate(positions):
            race_num = len(positions) - i  # Most recent = race 1
            
            # Create bar representation (inverse - shorter bar = better position)
            bar_length = max(1, int(((max_pos - pos + 1) / max_pos) * 20))
            bar = "█" * bar_length
            
            # Position indicator
            pos_text = "第1名" if pos == 1 else "第2名" if pos == 2 else "第3名" if pos == 3 else f"第{pos}名"
            
            chart_text += f"第{race_num:2d}場: {bar} ({pos_text})\n"
        
        # Add trend analysis
        if len(positions) >= 3:
            recent_avg = sum(positions[:3]) / 3
            older_avg = sum(positions[3:]) / len(positions[3:]) if len(positions) > 3 else recent_avg
            
            trend = "改善中" if recent_avg < older_avg else "下降中" if recent_avg > older_avg else "穩定"
            chart_text += f"\n趨勢: {trend}\n"
            chart_text += f"近期平均: {recent_avg:.1f}\n"
            chart_text += f"最佳: {min(positions)} | 最差: {max(positions)}"
        
        current_widget.chart.setText(chart_text)
    
    def _load_weight_analysis(self):
        """Analyze weight vs performance"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN CAST(SUBSTR(weight, 1, 3) AS INTEGER) < 110 THEN "低於110kg"
                    WHEN CAST(SUBSTR(weight, 1, 3) AS INTEGER) < 120 THEN "110-119kg"
                    WHEN CAST(SUBSTR(weight, 1, 3) AS INTEGER) < 130 THEN "120-129kg"
                    ELSE "130kg或以上"
                END as category,
                COUNT(*) as total,
                SUM(CASE WHEN position = 1 THEN 1 ELSE 0 END) as wins,
                ROUND(SUM(CASE WHEN position = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as win_rate
            FROM race_results
            WHERE weight IS NOT NULL AND weight != '' AND weight != '0'
            GROUP BY category
            ORDER BY category
        """)
        
        self._display_tab_results(cursor.fetchall())
    
    def _load_distance_analysis(self):
        """Analyze distance performance"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                race_distance as category,
                COUNT(*) as total,
                SUM(CASE WHEN position = 1 THEN 1 ELSE 0 END) as wins,
                ROUND(SUM(CASE WHEN position = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as win_rate
            FROM race_results
            WHERE race_distance IS NOT NULL AND race_distance != ''
            GROUP BY race_distance
            ORDER BY win_rate DESC
            LIMIT 15
        """)
        
        self._display_tab_results(cursor.fetchall())
    
    def _display_tab_results(self, rows):
        """Display results in current tab's table"""
        current_widget = self.tab_widget.currentWidget()
        if not hasattr(current_widget, 'table'):
            return
            
        table = current_widget.table
        table.setRowCount(len(rows))
        
        for row_idx, row in enumerate(rows):
            table.setItem(row_idx, 0, QTableWidgetItem(str(row[0])))
            table.setItem(row_idx, 1, QTableWidgetItem(str(row[1])))
            table.setItem(row_idx, 2, QTableWidgetItem(str(row[2])))
            table.setItem(row_idx, 3, QTableWidgetItem(f"{row[3]:.1f}%" if row[3] else "0%"))
    
    def _tab_style(self) -> str:
        return """
            QTabWidget::pane {
                border: 1px solid #334155;
                border-radius: 8px;
                background-color: #0f172a;
            }
            QTabBar::tab {
                background-color: #1e293b;
                color: #cbd5e1;
                padding: 12px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                min-width: 120px;
            }
            QTabBar::tab:selected {
                background-color: #3b82f6;
                color: #ffffff;
            }
            QTabBar::tab:hover:!selected {
                background-color: #334155;
            }
        """
    
    def _table_style(self) -> str:
        return """
            QTableWidget {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 6px;
                gridline-color: #334155;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #334155;
            }
            QTableWidget::item:selected {
                background-color: #3b82f6;
            }
            QHeaderView::section {
                background-color: #334155;
                color: #f8fafc;
                padding: 10px;
                border: none;
                font-weight: 600;
            }
        """
    def _combo_style(self) -> str:
        return """
            QComboBox {
                background-color: #0f172a;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px;
                min-width: 200px;
            }
            QComboBox::drop-down {
                border: none;
            }
        """

    def retranslate_ui(self):
        """Update UI strings after language change"""
        # Clear existing tabs and recreate them with translated names
        self.tab_widget.clear()

        # Recreate analysis tabs with translated names
        self._create_analysis_tabs()

        # Reload data for current tab
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            self.on_tab_changed(current_index)