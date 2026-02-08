#!/usr/bin/env python3
"""
Analysis Dashboard - Model validation, refinement analysis, and accuracy monitoring
Integrates with the PyQt racing analyzer
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QPushButton,
    QTextEdit, QTableWidget, QTableWidgetItem, QProgressBar, QSpinBox,
    QComboBox, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QColor
from datetime import datetime
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class AnalysisWorker(QThread):
    """Background worker for analysis tasks"""
    analysis_complete = pyqtSignal(dict)
    progress_update = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, analysis_type: str, **kwargs):
        super().__init__()
        self.analysis_type = analysis_type
        self.kwargs = kwargs
    
    def run(self):
        try:
            if self.analysis_type == 'validation':
                self._run_validation()
            elif self.analysis_type == 'barrier_analysis':
                self._run_barrier_analysis()
            elif self.analysis_type == 'model_comparison':
                self._run_model_comparison()
            elif self.analysis_type == 'retrain':
                self._run_retraining()
        except Exception as e:
            self.error.emit(str(e))
    
    def _run_validation(self):
        """Run prediction validation"""
        self.progress_update.emit("Loading validation module...")
        from backup.validate_predictions import PredictionValidator
        
        validator = PredictionValidator()
        self.progress_update.emit("Validating predictions...")
        results = validator.validate_all()
        
        self.analysis_complete.emit({
            'type': 'validation',
            'results': results
        })
    
    def _run_barrier_analysis(self):
        """Run barrier position analysis"""
        self.progress_update.emit("Analyzing barrier position feature...")
        from backup.refine_barrier_analysis import BarrierAnalyzer
        
        analyzer = BarrierAnalyzer()
        self.progress_update.emit("Running barrier statistics...")
        analyzer.run_full_analysis()
        
        self.analysis_complete.emit({
            'type': 'barrier_analysis',
            'status': 'completed'
        })
    
    def _run_model_comparison(self):
        """Run model comparison (V2 vs V3)"""
        self.progress_update.emit("Training comparison model without barriers...")
        from backup.model_xgboost_v3_no_barrier import XGBoostRacingModelV3
        
        model = XGBoostRacingModelV3()
        self.progress_update.emit("Building training dataset...")
        metrics = model.build_and_train()
        model.save_model()
        
        self.analysis_complete.emit({
            'type': 'model_comparison',
            'metrics': metrics
        })
    
    def _run_retraining(self):
        """Run automated retraining"""
        self.progress_update.emit("Starting automated retraining pipeline...")
        from backup.retrain_pipeline import RetrainingPipeline
        
        pipeline = RetrainingPipeline()
        self.progress_update.emit("Scraping new race data...")
        result = pipeline.run_full_pipeline(days_back=7)
        
        self.analysis_complete.emit({
            'type': 'retraining',
            'result': result
        })


class AnalysisDashboard(QWidget):
    """Dashboard for model analysis and monitoring"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Model Analysis & Monitoring")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Tab widget
        tabs = QTabWidget()
        tabs.addTab(self._create_validation_tab(), "Validation")
        tabs.addTab(self._create_refinement_tab(), "Refinement")
        tabs.addTab(self._create_monitoring_tab(), "Monitoring")
        layout.addWidget(tabs)
        
        self.setLayout(layout)
    
    def _create_validation_tab(self) -> QWidget:
        """Create prediction validation tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Description
        desc = QLabel(
            "Compare model predictions against actual race outcomes.\n"
            "Calculates accuracy, confidence calibration, and ROI metrics."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Date selector
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Race Date:"))
        self.validation_date = QComboBox()
        self._populate_validation_dates()
        date_layout.addWidget(self.validation_date)
        date_layout.addStretch()
        layout.addLayout(date_layout)
        
        # Results display
        self.validation_results = QTextEdit()
        self.validation_results.setReadOnly(True)
        self.validation_results.setPlaceholderText("Results will appear here...")
        layout.addWidget(self.validation_results)
        
        # Progress bar
        self.validation_progress = QProgressBar()
        self.validation_progress.setMaximum(0)
        self.validation_progress.setVisible(False)
        layout.addWidget(self.validation_progress)
        
        # Run button
        run_btn = QPushButton("Run Validation")
        run_btn.clicked.connect(self._run_validation)
        layout.addWidget(run_btn)
        
        widget.setLayout(layout)
        return widget
    
    def _create_refinement_tab(self) -> QWidget:
        """Create model refinement tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Description
        desc = QLabel(
            "Analyze model features and identify potential issues.\n"
            "Use the tools below to investigate feature importance and model performance."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Analysis selection
        analysis_layout = QHBoxLayout()
        analysis_layout.addWidget(QLabel("Select Analysis:"))
        self.analysis_type = QComboBox()
        self.analysis_type.addItems([
            "Barrier Position Analysis",
            "Feature Importance Comparison",
            "V2 vs V3 Model Comparison",
            "Feature Leakage Detection"
        ])
        analysis_layout.addWidget(self.analysis_type)
        analysis_layout.addStretch()
        layout.addLayout(analysis_layout)
        
        # Results display
        self.refinement_results = QTextEdit()
        self.refinement_results.setReadOnly(True)
        self.refinement_results.setPlaceholderText("Analysis results will appear here...")
        layout.addWidget(self.refinement_results)
        
        # Progress bar
        self.refinement_progress = QProgressBar()
        self.refinement_progress.setMaximum(0)
        self.refinement_progress.setVisible(False)
        layout.addWidget(self.refinement_progress)
        
        # Run button
        run_btn = QPushButton("Run Analysis")
        run_btn.clicked.connect(self._run_analysis)
        layout.addWidget(run_btn)
        
        widget.setLayout(layout)
        return widget
    
    def _create_monitoring_tab(self) -> QWidget:
        """Create accuracy monitoring tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Description
        desc = QLabel(
            "Monitor model accuracy over time.\n"
            "Track performance metrics and training history."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Stats table
        stats_table = QTableWidget()
        stats_table.setColumnCount(3)
        stats_table.setHorizontalHeaderLabels(["Metric", "Value", "Trend"])
        stats_table.setMaximumHeight(200)
        
        # Initialize with empty or loading states
        metrics = [
            ("Accuracy", "N/A", "-"),
            ("Precision", "N/A", "-"),
            ("Recall", "N/A", "-"),
            ("ROC-AUC", "N/A", "-"),
            ("Samples", "0", "-"),
            ("Model Version", "N/A", "-"),
        ]
        
        stats_table.setRowCount(len(metrics))
        for i, (metric, value, trend) in enumerate(metrics):
            stats_table.setItem(i, 0, QTableWidgetItem(metric))
            stats_table.setItem(i, 1, QTableWidgetItem(value))
            trend_item = QTableWidgetItem(trend)
            if "↑" in trend:
                trend_item.setForeground(QColor(76, 175, 80))
            stats_table.setItem(i, 2, trend_item)
        
        layout.addWidget(stats_table)
        
        # Retraining section
        retrain_group = QFrame()
        retrain_layout = QVBoxLayout()
        
        retrain_label = QLabel("Automated Retraining")
        retrain_label.setFont(QFont("Arial", 11, QFont.Bold))
        retrain_layout.addWidget(retrain_label)
        
        retrain_info = QLabel(
            "Model training information will be updated after the next run.\n"
            "Track performance metrics and model versions here."
        )
        retrain_layout.addWidget(retrain_info)
        
        # Retraining buttons
        button_layout = QHBoxLayout()
        
        now_btn = QPushButton("Retrain Now")
        now_btn.clicked.connect(self._run_retraining)
        button_layout.addWidget(now_btn)
        
        schedule_btn = QPushButton("Schedule Retraining")
        schedule_btn.clicked.connect(self._schedule_retraining)
        button_layout.addWidget(schedule_btn)
        
        button_layout.addStretch()
        retrain_layout.addLayout(button_layout)
        
        # Progress
        self.retrain_progress = QProgressBar()
        self.retrain_progress.setMaximum(0)
        self.retrain_progress.setVisible(False)
        retrain_layout.addWidget(self.retrain_progress)
        
        retrain_group.setLayout(retrain_layout)
        layout.addWidget(retrain_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def _run_validation(self):
        """Run prediction validation"""
        self.validation_progress.setVisible(True)
        self.validation_results.setText("Running validation...")
        
        self.worker = AnalysisWorker(
            'validation',
            race_date=self.validation_date.currentText()
        )
        self.worker.progress_update.connect(self._update_validation_progress)
        self.worker.analysis_complete.connect(self._on_validation_complete)
        self.worker.error.connect(self._on_validation_error)
        self.worker.start()
    
    def _run_analysis(self):
        """Run refinement analysis"""
        self.refinement_progress.setVisible(True)
        self.refinement_results.setText("Running analysis...")
        
        analysis_type_map = {
            "Barrier Position Analysis": "barrier_analysis",
            "Feature Importance Comparison": "barrier_analysis",
            "V2 vs V3 Model Comparison": "model_comparison",
            "Feature Leakage Detection": "barrier_analysis",
        }
        
        self.worker = AnalysisWorker(
            analysis_type_map.get(self.analysis_type.currentText(), "barrier_analysis")
        )
        self.worker.progress_update.connect(self._update_refinement_progress)
        self.worker.analysis_complete.connect(self._on_analysis_complete)
        self.worker.error.connect(self._on_analysis_error)
        self.worker.start()
    
    def _run_retraining(self):
        """Run automated retraining"""
        self.retrain_progress.setVisible(True)
        
        self.worker = AnalysisWorker('retrain')
        self.worker.progress_update.connect(self._update_retrain_progress)
        self.worker.analysis_complete.connect(self._on_retrain_complete)
        self.worker.error.connect(self._on_retrain_error)
        self.worker.start()
    
    def _schedule_retraining(self):
        """Schedule automated retraining"""
        # Implementation for scheduling
        pass
    
    def _update_validation_progress(self, message: str):
        """Update validation progress"""
        self.validation_results.setText(message)
    
    def _update_refinement_progress(self, message: str):
        """Update refinement progress"""
        self.refinement_results.setText(message)
    
    def _update_retrain_progress(self, message: str):
        """Update retraining progress"""
        # Could show progress bar
        pass
    
    def _on_validation_complete(self, result: dict):
        """Handle validation completion"""
        self.validation_progress.setVisible(False)
        text = f"""
VALIDATION REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M')}
{'=' * 60}

✓ Validation complete
Status: {result.get('type', 'N/A')}

Check logs for detailed results.
        """
        self.validation_results.setText(text)
    
    def _on_analysis_complete(self, result: dict):
        """Handle analysis completion"""
        self.refinement_progress.setVisible(False)
        text = f"""
ANALYSIS COMPLETE - {datetime.now().strftime('%Y-%m-%d %H:%M')}
{'=' * 60}

✓ Analysis finished
Type: {result.get('type', 'N/A')}

KEY FINDINGS:
{result.get('findings', 'No significant findings recorded.')}

Check logs for detailed results.
        """
        self.refinement_results.setText(text)
    
    def _on_retrain_complete(self, result: dict):
        """Handle retraining completion"""
        status = result.get('result', {}).get('status', 'unknown')
        version = result.get('result', {}).get('version', 'N/A')
        
        message = f"✓ Retraining complete! Model {version} trained."
        if status != 'success':
            message = "✗ Retraining failed. Check logs for details."
        
        # Could use QMessageBox
        # QMessageBox.information(self, "Retraining", message)
    
    def _on_validation_error(self, error: str):
        """Handle validation error"""
        self.validation_progress.setVisible(False)
        self.validation_results.setText(f"ERROR: {error}")
    
    def _on_analysis_error(self, error: str):
        """Handle analysis error"""
        self.refinement_progress.setVisible(False)
        self.refinement_results.setText(f"ERROR: {error}")
    
    def _on_retrain_error(self, error: str):
        """Handle retraining error"""
        self.retrain_progress.setVisible(False)
        # Could show error dialog
        logger.error(f"Retraining error: {error}")

    def _populate_validation_dates(self):
        """Populate validation date dropdown with distinct dates from future_race_cards"""
        try:
            import os
            import sqlite3
            db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'hkjc_races.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Get distinct dates from future_race_cards
            cursor.execute('SELECT DISTINCT race_date FROM future_race_cards ORDER BY race_date')
            dates = [row[0] for row in cursor.fetchall()]
            conn.close()

            if dates:
                self.validation_date.clear()
                self.validation_date.addItems(dates)
            else:
                self.validation_date.addItem("No dates available")

        except Exception as e:
            logger.error(f"Error populating validation dates: {e}")
            self.validation_date.addItem("Error loading dates")
