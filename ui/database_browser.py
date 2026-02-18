
#!/usr/bin/env python3
"""
Database Browser - Modern interface for viewing and filtering database tables
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QTableWidget,
    QTableWidgetItem, QLabel, QLineEdit, QPushButton, QDateEdit, QComboBox, 
    QSpinBox, QFrame, QGridLayout, QSizePolicy, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, QDate, QSize
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon
import sqlite3
import pandas as pd
import os


class DatabaseBrowser(QWidget):
    """Modern database browser with filtering capabilities"""
    
    def __init__(self, db_path: str = None, parent=None):
        super().__init__(parent)
        if db_path is None:
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'hkjc_races.db')
        self.db_path = db_path
        print(f"Database path: {self.db_path}")
        print(f"Database exists: {os.path.exists(self.db_path)}")
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        
        self.current_table = None
        self.current_df = None
        self.filtered_df = None
        self.current_page = 0
        self.rows_per_page = 25
        
        self.init_ui()
        self.load_tables()
        self.setup_styles()
    
    def init_ui(self):
        """Initialize modern UI layout"""
        self.setObjectName("databaseBrowser")
        
        # Main layout with subtle spacing
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(24)
        
        # Left sidebar - Clean and minimal
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(12)
        
        # Sidebar header
        sidebar_header = QLabel(self.tr("數據庫"))
        sidebar_header.setFont(QFont("Segoe UI", 13, QFont.Bold))
        sidebar_header.setStyleSheet("""
            color: #94a3b8;
            padding-bottom: 4px;
            border-bottom: 1px solid #334155;
        """)
        sidebar_header.setFixedHeight(40)
        sidebar_layout.addWidget(sidebar_header)
        
        # Table list with modern styling
        self.table_list = QListWidget()
        self.table_list.setObjectName("tableList")
        self.table_list.setFont(QFont("Segoe UI", 10))
        self.table_list.itemClicked.connect(self.on_table_selected)
        self.table_list.setAlternatingRowColors(True)
        sidebar_layout.addWidget(self.table_list)
        
        # Database info panel
        info_frame = QFrame()
        info_frame.setObjectName("infoFrame")
        info_frame.setMaximumHeight(120)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(12, 12, 12, 12)
        
        db_info = QLabel(self.tr("數據庫信息"))
        db_info.setFont(QFont("Segoe UI", 10, QFont.Bold))
        db_info.setStyleSheet("color: #cbd5e1; margin-bottom: 8px;")
        info_layout.addWidget(db_info)
        
        self.db_stats = QLabel(self.tr("請選擇表格以查看數據"))
        self.db_stats.setFont(QFont("Segoe UI", 9))
        self.db_stats.setStyleSheet("color: #94a3b8;")
        self.db_stats.setWordWrap(True)
        info_layout.addWidget(self.db_stats)
        info_layout.addStretch()
        
        sidebar_layout.addWidget(info_frame)
        main_layout.addLayout(sidebar_layout)
        
        # Right content area
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)
        
        # Main header
        header_container = QHBoxLayout()
        self.header_label = QLabel(self.tr("數據庫瀏覽器"))
        self.header_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
        self.header_label.setStyleSheet("color: #f8fafc;")
        header_container.addWidget(self.header_label)
        
        header_container.addStretch()
        
        self.export_btn = QPushButton(self.tr("導出CSV"))
        self.export_btn.setObjectName("secondaryButton")
        self.export_btn.clicked.connect(self.export_data)
        header_container.addWidget(self.export_btn)
        
        self.refresh_btn = QPushButton(self.tr("刷新"))
        self.refresh_btn.setObjectName("primaryButton")
        self.refresh_btn.clicked.connect(self.refresh_data)
        header_container.addWidget(self.refresh_btn)
        
        content_layout.addLayout(header_container)
        
        # Filter panel - Clean grid layout
        filter_frame = QFrame()
        filter_frame.setObjectName("filterFrame")
        filter_frame.setMaximumHeight(140)
        
        filter_layout = QGridLayout(filter_frame)
        filter_layout.setContentsMargins(20, 20, 20, 20)
        filter_layout.setHorizontalSpacing(20)
        filter_layout.setVerticalSpacing(12)
        
        # Search row
        filter_layout.addWidget(QLabel(self.tr("快速搜索:")), 0, 0)
        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText(self.tr("在所有列中搜索..."))
        self.search_input.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.search_input, 0, 1, 1, 2)
        
        # Clear filters button
        self.clear_btn = QPushButton(self.tr("清除過濾器"))
        self.clear_btn.setObjectName("textButton")
        self.clear_btn.clicked.connect(self.clear_filters)
        filter_layout.addWidget(self.clear_btn, 0, 3)
        
        content_layout.addWidget(filter_frame)
        
        # Table area with header
        table_header = QHBoxLayout()
        
        self.table_info = QLabel(self.tr("未選擇表格"))
        self.table_info.setFont(QFont("Segoe UI", 11, QFont.Medium))
        self.table_info.setStyleSheet("color: #cbd5e1;")
        table_header.addWidget(self.table_info)
        
        table_header.addStretch()
        
        self.row_count_label = QLabel("")
        self.row_count_label.setFont(QFont("Segoe UI", 10))
        self.row_count_label.setStyleSheet("color: #94a3b8;")
        table_header.addWidget(self.row_count_label)
        
        content_layout.addLayout(table_header)
        
        # Data table
        self.table = QTableWidget()
        self.table.setObjectName("dataTable")
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSortingEnabled(True)
        content_layout.addWidget(self.table)
        
        # Pagination controls
        pagination_frame = QFrame()
        pagination_frame.setObjectName("paginationFrame")
        pagination_frame.setMaximumHeight(60)
        
        pagination_layout = QHBoxLayout(pagination_frame)
        pagination_layout.setContentsMargins(20, 12, 20, 12)
        
        # Left side - page controls
        control_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("←")
        self.prev_btn.setObjectName("iconButton")
        self.prev_btn.setFixedSize(40, 32)
        self.prev_btn.clicked.connect(self.prev_page)
        control_layout.addWidget(self.prev_btn)
        
        self.page_info = QLabel(self.tr("沒有數據"))
        self.page_info.setFont(QFont("Segoe UI", 10))
        self.page_info.setStyleSheet("color: #cbd5e1; padding: 0 12px;")
        control_layout.addWidget(self.page_info)
        
        self.next_btn = QPushButton("→")
        self.next_btn.setObjectName("iconButton")
        self.next_btn.setFixedSize(40, 32)
        self.next_btn.clicked.connect(self.next_page)
        control_layout.addWidget(self.next_btn)
        
        pagination_layout.addLayout(control_layout)
        
        pagination_layout.addStretch()
        
        # Right side - rows per page
        rows_layout = QHBoxLayout()
        
        rows_layout.addWidget(QLabel(self.tr("每頁行數:")))
        
        self.rows_spin = QSpinBox()
        self.rows_spin.setObjectName("rowsSpin")
        self.rows_spin.setRange(10, 100)
        self.rows_spin.setValue(25)
        self.rows_spin.setSingleStep(5)
        self.rows_spin.setFixedWidth(80)
        self.rows_spin.valueChanged.connect(self.on_rows_changed)
        rows_layout.addWidget(self.rows_spin)
        
        pagination_layout.addLayout(rows_layout)
        
        content_layout.addWidget(pagination_frame)
        
        main_layout.addLayout(content_layout, 1)
        
        self.setLayout(main_layout)
    
    def setup_styles(self):
        """Setup modern CSS styles"""
        self.setStyleSheet("""
            #databaseBrowser {
                background-color: #0f172a;
            }
            
            /* Table List */
            #tableList {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #f8fafc;
                outline: none;
            }
            
            #tableList::item {
                padding: 10px 16px;
                border-radius: 6px;
                margin: 2px 4px;
            }
            
            #tableList::item:selected {
                background-color: #3b82f6;
                color: #ffffff;
            }
            
            #tableList::item:hover:!selected {
                background-color: #334155;
            }
            
            /* Info Frame */
            #infoFrame {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
            }
            
            /* Filter Frame */
            #filterFrame {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 10px;
            }
            
            QLabel {
                color: #cbd5e1;
                font-family: 'Segoe UI';
            }
            
            /* Search Input */
            #searchInput {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #f8fafc;
                padding: 10px 14px;
                font-family: 'Segoe UI';
                font-size: 13px;
            }
            
            #searchInput:focus {
                border: 1px solid #3b82f6;
                outline: none;
            }
            
            /* Date Input */
            #dateInput {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #f8fafc;
                padding: 8px 12px;
                font-family: 'Segoe UI';
                min-width: 120px;
            }
            
            /* Buttons */
            #primaryButton {
                background-color: #3b82f6;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-family: 'Segoe UI Semibold';
                font-size: 13px;
                min-height: 40px;
            }
            
            #primaryButton:hover {
                background-color: #2563eb;
            }
            
            #primaryButton:pressed {
                background-color: #1d4ed8;
            }
            
            #secondaryButton {
                background-color: #475569;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-family: 'Segoe UI Semibold';
                font-size: 13px;
                min-height: 40px;
            }
            
            #secondaryButton:hover {
                background-color: #334155;
            }
            
            #textButton {
                background-color: transparent;
                color: #94a3b8;
                border: none;
                padding: 8px 16px;
                font-family: 'Segoe UI';
                font-size: 13px;
                text-decoration: underline;
            }
            
            #textButton:hover {
                color: #cbd5e1;
            }
            
            #iconButton {
                background-color: #334155;
                color: #f8fafc;
                border: none;
                border-radius: 6px;
                font-family: 'Segoe UI';
                font-size: 14px;
                font-weight: bold;
            }
            
            #iconButton:hover {
                background-color: #475569;
            }
            
            #iconButton:disabled {
                background-color: #1e293b;
                color: #64748b;
            }
            
            /* Data Table */
            #dataTable {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                gridline-color: #334155;
                outline: none;
            }
            
            #dataTable::item {
                padding: 12px 16px;
                border: none;
                color: #f8fafc;
                font-family: 'Segoe UI';
                font-size: 13px;
            }
            
            #dataTable::item:selected {
                background-color: #334155;
            }
            
            #dataTable::item:alternate {
                background-color: #1a243b;
            }
            
            QHeaderView::section {
                background-color: #0f172a;
                color: #cbd5e1;
                padding: 14px 16px;
                border: none;
                border-right: 1px solid #334155;
                font-family: 'Segoe UI Semibold';
                font-size: 13px;
            }
            
            QHeaderView::section:last {
                border-right: none;
            }
            
            /* Pagination Frame */
            #paginationFrame {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
            }
            
            /* Rows Spin */
            #rowsSpin {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #f8fafc;
                padding: 6px 12px;
                font-family: 'Segoe UI';
                min-width: 80px;
            }
            
            #rowsSpin::up-button, #rowsSpin::down-button {
                background-color: #334155;
                border: none;
                border-radius: 3px;
                width: 20px;
            }
        """)
    
    def retranslate_ui(self):
        """Update UI strings after language change"""
        self.header_label.setText(self.tr("數據庫瀏覽器"))
        self.export_btn.setText(self.tr("導出CSV"))
        self.refresh_btn.setText(self.tr("刷新"))
        self.search_input.setPlaceholderText(self.tr("在所有列中搜索..."))
        self.clear_btn.setText(self.tr("清除過濾器"))
        self.update_table_info()
    
    def load_tables(self):
        """Load table names from database"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                ORDER BY name
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            print(f"Found {len(tables)} tables: {tables}")
            
            self.table_list.clear()
            for table in tables:
                item = QListWidgetItem(table)
                item.setFont(QFont("Arial", 10))
                self.table_list.addItem(item)
                print(f"Added table: {table}")
            
            # Update database stats
            self.db_stats.setText(self.tr(f"{len(tables)} 個表格可用"))
            
            # Auto-select first table if available
            if tables:
                self.table_list.setCurrentRow(0)
                self.current_table = tables[0]
                self.current_page = 0
                self.load_table_data()
                self.apply_filters()
                self.update_table_info()
            
        except Exception as e:
            print(f"Error loading tables: {e}")
            import traceback
            traceback.print_exc()
    
    def on_table_selected(self, item: QListWidgetItem):
        """Handle table selection"""
        self.current_table = item.text()
        self.current_page = 0
        self.load_table_data()
        self.apply_filters()
        self.update_table_info()
    
    def update_table_info(self):
        """Update table information display"""
        if self.current_table:
            if self.filtered_df is not None:
                count = len(self.filtered_df)
                self.table_info.setText(
                    self.tr(f"表格: {self.current_table} • {count:,} 條記錄")
                )
                self.row_count_label.setText(
                    self.tr(f"已過濾: {count:,} / {len(self.current_df):,}")
                )
            else:
                self.table_info.setText(self.tr(f"表格: {self.current_table}"))
        else:
            self.table_info.setText(self.tr("未選擇表格"))
            self.row_count_label.clear()
    
    def load_table_data(self):
        """Load all data from selected table"""
        if self.current_table is None:
            return
        
        try:
            # print(f"Loading data from table: {self.current_table}")
            query = f"SELECT * FROM {self.current_table}"
            self.current_df = pd.read_sql(query, self.conn)
            # print(f"Loaded {len(self.current_df)} rows from {self.current_table}")
            # print(f"Columns: {list(self.current_df.columns)}")
        except Exception as e:
            print(f"Error loading table {self.current_table}: {e}")
            import traceback
            traceback.print_exc()
            self.current_df = pd.DataFrame()
    
    def apply_filters(self):
        """Apply filter selections"""
        if self.current_df is None or self.current_df.empty:
            self.page_info.setText(self.tr("沒有數據"))
            return
        
        df = self.current_df.copy()
        
        # Search filter
        search_text = self.search_input.text().lower()
        if search_text:
            mask = df.astype(str).apply(lambda x: x.str.contains(search_text, case=False)).any(axis=1)
            df = df[mask]
        
        self.filtered_df = df
        self.current_page = 0
        self.display_page()
        self.update_table_info()
    
    def clear_filters(self):
        """Clear all filters"""
        self.search_input.clear()
        self.apply_filters()
    
    def display_page(self):
        """Display current page of data"""
        print(f"display_page called - filtered_df: {self.filtered_df is not None}, empty: {self.filtered_df.empty if self.filtered_df is not None else 'N/A'}")
        
        if self.filtered_df is None or self.filtered_df.empty:
            print("No data to display")
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            self.page_info.setText(self.tr("沒有結果"))
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            return
        
        start_idx = self.current_page * self.rows_per_page
        end_idx = min(start_idx + self.rows_per_page, len(self.filtered_df))
        page_data = self.filtered_df.iloc[start_idx:end_idx]
        
        print(f"Displaying rows {start_idx}-{end_idx} of {len(self.filtered_df)} total")
        print(f"Page data shape: {page_data.shape}")
        
        self.table.setColumnCount(len(page_data.columns))
        self.table.setHorizontalHeaderLabels(page_data.columns.tolist())
        self.table.setRowCount(len(page_data))
        
        for row_idx, (_, row) in enumerate(page_data.iterrows()):
            for col_idx, value in enumerate(row):
                item = QTableWidgetItem(str(value) if pd.notna(value) else "")
                item.setFont(QFont("Segoe UI", 11))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row_idx, col_idx, item)
        
        # Auto-resize columns
        self.table.resizeColumnsToContents()
        
        # Update pagination info
        total_pages = max(1, (len(self.filtered_df) + self.rows_per_page - 1) // self.rows_per_page)
        page_info = self.tr("第 {} 頁 / 共 {} 頁 • 記錄 {} - {} / 共 {}").format(
            self.current_page + 1, total_pages,
            start_idx + 1, end_idx, len(self.filtered_df)
        )
        self.page_info.setText(page_info)
        print(f"Set page info: {page_info}")
        
        # Enable/disable navigation buttons
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page < total_pages - 1)
    
    def next_page(self):
        """Go to next page"""
        if self.filtered_df is not None and not self.filtered_df.empty:
            total_pages = (len(self.filtered_df) + self.rows_per_page - 1) // self.rows_per_page
            if self.current_page < total_pages - 1:
                self.current_page += 1
                self.display_page()
    
    def prev_page(self):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self.display_page()
    
    def on_rows_changed(self, value: int):
        """Handle rows per page change"""
        self.rows_per_page = value
        self.current_page = 0
        self.display_page()
    
    def export_data(self):
        """Export current view to CSV"""
        # Ensure we have the latest data if none is currently loaded
        if self.current_df is None or self.current_df.empty:
            if self.current_table:
                self.load_table_data()
            else:
                # No table selected - show warning
                QMessageBox.warning(
                    self,
                    self.tr("沒有數據"),
                    self.tr("沒有可導出的數據。請先選擇一個表格並點擊刷新。")
                )
                return
        
        # Apply filters and check if we have data
        self.apply_filters()

        if self.filtered_df is not None and not self.filtered_df.empty:
            # Show file save dialog
            default_filename = f"{self.current_table}_export.csv"
            filename, _ = QFileDialog.getSaveFileName(
                self,
                self.tr("導出CSV文件"),
                default_filename,
                "CSV Files (*.csv);;All Files (*)"
            )
            
            if filename:
                try:
                    # Use a robust encoding strategy
                    try:
                        self.filtered_df.to_csv(filename, index=False, encoding='utf-8-sig')
                    except UnicodeEncodeError:
                        self.filtered_df.to_csv(filename, index=False, encoding='utf-8')
                        
                    QMessageBox.information(
                        self,
                        self.tr("導出成功"),
                        self.tr(f"數據已成功導出到:\n{filename}")
                    )
                    print(f"Exported to {filename}")
                except Exception as e:
                    import traceback
                    error_details = traceback.format_exc()
                    print(f"Export error: {error_details}")
                    QMessageBox.critical(
                        self,
                        self.tr("導出失敗"),
                        self.tr(f"導出時發生錯誤:\n{str(e)}")
                    )
            else:
                # User cancelled
                print("Export cancelled by user")
        else:
            QMessageBox.warning(
                self,
                self.tr("沒有數據"),
                self.tr("沒有可導出的數據。請先選擇一個表格並點擊刷新。")
            )
    
    def refresh_data(self):
        """Refresh data from database"""
        # Close and reopen connection to ensure fresh data
        if self.conn:
            self.conn.close()
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
        if self.current_table:
            self.load_table_data()
            self.apply_filters()
            print(f"Refreshed {self.current_table}")
        else:
            # Refresh table list
            self.table_list.clear()
            self.load_tables()
            print("Refreshed table list")
    def closeEvent(self, event):
        """Clean up database connection"""
        if self.conn:
            self.conn.close()
        super().closeEvent(event)