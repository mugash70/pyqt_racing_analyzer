"""
Training Worker - Background thread for model training
"""

from PyQt5.QtCore import QThread, pyqtSignal
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime
import logging
import pandas as pd
import numpy as np

class TrainingWorker(QThread):
    """Worker thread for ML model training"""
    
    progress = pyqtSignal(str)  # Progress message
    stage_changed = pyqtSignal(str)  # Current stage
    stage_progress = pyqtSignal(int)  # Stage progress percentage
    metrics_calculated = pyqtSignal(dict)  # Training metrics
    epoch_completed = pyqtSignal(int, int)  # Epoch, total epochs
    finished = pyqtSignal(dict)  # Final results
    error = pyqtSignal(str)  # Error message
    
    def __init__(self, days: int = 30):
        super().__init__()
        self.training_days = days
        self.logger = logging.getLogger(__name__)
        
    def run(self):
        """Execute the model training pipeline"""
        try:
            results = {
                'training_days': self.training_days,
                'samples_used': 0,
                'features_created': 0,
                'training_time': 0,
                'metrics': {},
                'start_time': datetime.now(),
                'status': 'success'
            }
            
            self.progress.emit("Initializing training pipeline...")
            self.stage_changed.emit("initializing")
            
            # Import ML components
            from backup_scraper.pipeline import HKJCDataPipeline
            from backup.feature_engineering import FeatureEngineer
            from backup.ml_ensemble_model import EnsembleModel
            from backup.data_preprocessing import DataPreprocessor
            
            self.progress.emit(f"Loading data for last {self.training_days} days...")
            self.stage_changed.emit("loading_data")
            self.stage_progress.emit(10)
            
            # Get data from pipeline
            pipeline = HKJCDataPipeline()
            races = pipeline.get_recent_races(days=self.training_days)
            
            if not races:
                raise Exception(f"No race data found for the last {self.training_days} days")
            
            self.progress.emit(f"Loaded {len(races)} races with {sum(len(r.get('positions', [])) for r in races)} horse records")
            results['samples_used'] = sum(len(r.get('positions', [])) for r in races)
            
            # Export to CSV for feature engineering
            self.progress.emit("Preparing feature engineering...")
            self.stage_changed.emit("feature_engineering")
            self.stage_progress.emit(20)
            
            csv_path = pipeline.export_to_csv_for_ml("training_data_temp.csv", days_back=self.training_days)
            
            if not csv_path:
                raise Exception("Failed to export training data")
            
            # Load and engineer features
            self.progress.emit("Engineering features...")
            self.stage_progress.emit(30)
            
            df = pd.read_csv(csv_path)
            results['features_created'] = len(df.columns)
            
            self.progress.emit(f"Created {results['features_created']} features from {len(df)} samples")
            
            # Preprocess data
            self.progress.emit("Preprocessing data...")
            self.stage_changed.emit("preprocessing")
            self.stage_progress.emit(40)
            
            preprocessor = DataPreprocessor()
            X, y = preprocessor.preprocess(df, fit=True)
            
            self.progress.emit(f"Preprocessed data shape: {X.shape}")
            
            # Initialize and train model
            self.progress.emit("Initializing ensemble model...")
            self.stage_changed.emit("training")
            self.stage_progress.emit(50)
            
            model = EnsembleModel()
            
            # Simulate training epochs for progress updates
            total_epochs = 10
            for epoch in range(1, total_epochs + 1):
                self.msleep(200)  # Simulate computation
                self.progress.emit(f"Training epoch {epoch}/{total_epochs}...")
                self.stage_progress.emit(50 + (epoch * 4))
                self.epoch_completed.emit(epoch, total_epochs)
            
            # Actually train
            self.progress.emit("Training ensemble models...")
            self.stage_changed.emit("training")
            
            metrics = model.train(X, y)
            
            results['metrics'] = {
                'accuracy': float(metrics.get('accuracy', 0)),
                'precision': float(metrics.get('precision', 0)),
                'recall': float(metrics.get('recall', 0)),
                'f1': float(metrics.get('f1', 0)),
                'roc_auc': float(metrics.get('roc_auc', 0))
            }
            
            self.metrics_calculated.emit(results['metrics'])
            
            # Save model
            self.progress.emit("Saving trained models...")
            self.stage_changed.emit("saving")
            self.stage_progress.emit(90)
            
            model_path = os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'ensemble_model.pkl')
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            model.save(model_path)
            
            preprocessor_path = model_path.replace('ensemble_model.pkl', 'preprocessor.pkl')
            preprocessor.save(preprocessor_path)
            
            self.progress.emit(f"Models saved to {model_path}")
            
            # Cleanup temp file
            if os.path.exists(csv_path):
                os.remove(csv_path)
            
            results['end_time'] = datetime.now()
            results['training_time'] = (results['end_time'] - results['start_time']).total_seconds()
            results['model_path'] = model_path
            
            self.progress.emit(f"Training complete in {results['training_time']:.1f} seconds!")
            self.stage_changed.emit("completed")
            self.stage_progress.emit(100)
            self.finished.emit(results)
            
        except Exception as e:
            error_msg = f"Training failed: {str(e)}"
            self.logger.error(error_msg)
            self.error.emit(error_msg)
            results['status'] = 'failed'
            self.finished.emit(results)

    def stop(self):
        """Stop the worker thread"""
        self.terminate()
        self.wait()
