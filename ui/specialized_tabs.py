from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QTextEdit, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import sqlite3
import os

class RaceReportsTab(QWidget):
    def __init__(self, db_path, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["日期", "賽事", "報告摘要"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.itemClicked.connect(self.show_full_report)
        layout.addWidget(self.table)
        
        self.report_display = QTextEdit()
        self.report_display.setReadOnly(True)
        self.report_display.setMaximumHeight(200)
        layout.addWidget(self.report_display)
        
        self.load_data()

    def load_data(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT race_date, race_number, report_text FROM race_reports ORDER BY race_date DESC LIMIT 50")
            rows = cursor.fetchall()
            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.table.setItem(i, 1, QTableWidgetItem(str(row[1])))
                snippet = str(row[2])[:100] + "..." if row[2] else ""
                item = QTableWidgetItem(snippet)
                item.setData(Qt.UserRole, row[2])
                self.table.setItem(i, 2, item)
        except Exception as e:
            # Handle missing data gracefully
            self.table.setRowCount(1)
            self.table.setItem(0, 0, QTableWidgetItem("無數據"))
            self.table.setItem(0, 1, QTableWidgetItem("-"))
            self.table.setItem(0, 2, QTableWidgetItem(f"錯誤: {e}"))
        conn.close()

    def show_full_report(self, item):
        if item.column() == 2:
            self.report_display.setText(item.data(Qt.UserRole))

class ExerciseDataTab(QWidget):
    def __init__(self, db_path, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["日期", "馬匹", "晨操資訊"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        layout.addWidget(self.table)
        self.load_data()

    def load_data(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT race_date, horse_name, trackwork_time FROM morning_trackwork ORDER BY race_date DESC LIMIT 100")
            rows = cursor.fetchall()
            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.table.setItem(i, 1, QTableWidgetItem(str(row[1])))
                self.table.setItem(i, 2, QTableWidgetItem(str(row[2])))
        except Exception as e:
            self.table.setRowCount(1)
            self.table.setItem(0, 0, QTableWidgetItem("無數據"))
            self.table.setItem(0, 1, QTableWidgetItem("-"))
            self.table.setItem(0, 2, QTableWidgetItem(f"錯誤: {e}"))
        conn.close()

class ProfessionalSchedulesTab(QWidget):
    def __init__(self, db_path, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["類型", "姓名", "賽事日期", "出賽/策騎"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        self.load_data()

    def load_data(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT professional_type, professional_name, race_date, horse_name FROM professional_schedules ORDER BY race_date DESC LIMIT 100")
            rows = cursor.fetchall()
            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.table.setItem(i, 1, QTableWidgetItem(str(row[1])))
                self.table.setItem(i, 2, QTableWidgetItem(str(row[2])))
                self.table.setItem(i, 3, QTableWidgetItem(str(row[3])))
        except Exception as e:
            self.table.setRowCount(1)
            self.table.setItem(0, 0, QTableWidgetItem("無數據"))
            self.table.setItem(0, 1, QTableWidgetItem("-"))
            self.table.setItem(0, 2, QTableWidgetItem("-"))
            self.table.setItem(0, 3, QTableWidgetItem(f"錯誤: {e}"))
        conn.close()
