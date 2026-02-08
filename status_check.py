#!/usr/bin/env python3
"""
Comprehensive Status Checker for PyQt Racing Analyzer
Verifies all components are working correctly
"""

import os
import sys
import sqlite3
import importlib
from pathlib import Path
from datetime import datetime

class StatusChecker:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.successes = []
        
    def check_dependencies(self):
        """Check all required Python packages"""
        print("📦 Checking Python Dependencies...")
        
        required_packages = {
            'PyQt5': 'PyQt5.QtWidgets',
            'pandas': 'pandas',
            'numpy': 'numpy', 
            'sklearn': 'sklearn',
            'xgboost': 'xgboost',
            'lightgbm': 'lightgbm',
            'requests': 'requests',
            'bs4': 'bs4'
        }
        
        for name, import_name in required_packages.items():
            try:
                importlib.import_module(import_name)
                self.successes.append(f"✅ {name}")
                print(f"  ✅ {name}")
            except ImportError:
                self.issues.append(f"❌ {name} - Not installed")
                print(f"  ❌ {name} - Not installed")
    
    def check_database(self):
        """Check database structure and data"""
        print("\n💾 Checking Database...")
        
        db_path = Path("database/hkjc_races.db")
        if not db_path.exists():
            self.issues.append("❌ Database file not found")
            print("  ❌ Database file not found")
            return
        
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Check key tables
            key_tables = [
                'race_results', 'future_race_cards', 'horses', 
                'jockey_stats', 'trainer_stats', 'barrier_draws'
            ]
            
            for table in key_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                if count > 0:
                    self.successes.append(f"✅ {table}: {count} records")
                    print(f"  ✅ {table}: {count:,} records")
                else:
                    self.warnings.append(f"⚠️ {table}: No data")
                    print(f"  ⚠️ {table}: No data")
            
            conn.close()
            
        except Exception as e:
            self.issues.append(f"❌ Database error: {e}")
            print(f"  ❌ Database error: {e}")
    
    def check_ui_components(self):
        """Check UI components can be imported"""
        print("\n🖥️ Checking UI Components...")
        
        ui_modules = [
            'ui.styles',
            'ui.home_page', 
            'ui.analysis_tab',
            'ui.loading_screen',
            'ui.prediction_detail_modal'
        ]
        
        for module in ui_modules:
            try:
                importlib.import_module(module)
                self.successes.append(f"✅ {module}")
                print(f"  ✅ {module}")
            except ImportError as e:
                self.issues.append(f"❌ {module}: {e}")
                print(f"  ❌ {module}: {e}")
    
    def check_ml_service(self):
        """Check ML service functionality"""
        print("\n🤖 Checking ML Service...")
        
        try:
            from ml.ml_service import MLService
            
            # Try to initialize ML service
            ml_service = MLService()
            self.successes.append("✅ ML Service initialized")
            print("  ✅ ML Service initialized")
            
            # Check if model can be loaded
            if ml_service.ml_model:
                self.successes.append("✅ ML Model loaded")
                print("  ✅ ML Model loaded")
            else:
                self.warnings.append("⚠️ ML Model not loaded")
                print("  ⚠️ ML Model not loaded")
            
            # Test prediction capability
            races = ml_service.get_available_races()
            if races:
                self.successes.append(f"✅ Found {len(races)} races for prediction")
                print(f"  ✅ Found {len(races)} races for prediction")
            else:
                self.warnings.append("⚠️ No races available for prediction")
                print("  ⚠️ No races available for prediction")
                
        except Exception as e:
            self.issues.append(f"❌ ML Service error: {e}")
            print(f"  ❌ ML Service error: {e}")
    
    def check_translations(self):
        """Check translation files"""
        print("\n🌐 Checking Translations...")
        
        i18n_dir = Path("i18n")
        if not i18n_dir.exists():
            self.warnings.append("⚠️ i18n directory not found")
            print("  ⚠️ i18n directory not found")
            return
        
        translation_files = list(i18n_dir.glob("*.qm"))
        if translation_files:
            for file in translation_files:
                self.successes.append(f"✅ Translation: {file.name}")
                print(f"  ✅ Translation: {file.name}")
        else:
            self.warnings.append("⚠️ No compiled translation files found")
            print("  ⚠️ No compiled translation files found")
    
    def check_main_application(self):
        """Check main application can start"""
        print("\n🚀 Checking Main Application...")
        
        main_file = Path("main.py")
        if not main_file.exists():
            self.issues.append("❌ main.py not found")
            print("  ❌ main.py not found")
            return
        
        try:
            # Try to import main components without running
            sys.path.insert(0, str(Path.cwd()))
            
            # Check if we can import the main window class
            with open("main.py", "r") as f:
                content = f.read()
                if "class MainWindow" in content:
                    self.successes.append("✅ MainWindow class found")
                    print("  ✅ MainWindow class found")
                else:
                    self.issues.append("❌ MainWindow class not found")
                    print("  ❌ MainWindow class not found")
            
            # Check critical imports
            critical_imports = [
                "from PyQt5.QtWidgets import",
                "from ui.styles import",
                "from ui.home_page import"
            ]
            
            for import_line in critical_imports:
                if import_line in content:
                    self.successes.append(f"✅ Import: {import_line.split(' import')[0]}")
                    print(f"  ✅ Import: {import_line.split(' import')[0]}")
                else:
                    self.warnings.append(f"⚠️ Missing import: {import_line}")
                    print(f"  ⚠️ Missing import: {import_line}")
                    
        except Exception as e:
            self.issues.append(f"❌ Main application error: {e}")
            print(f"  ❌ Main application error: {e}")
    
    def check_build_readiness(self):
        """Check if ready for building"""
        print("\n🏗️ Checking Build Readiness...")
        
        # Check PyInstaller
        try:
            import PyInstaller
            self.successes.append("✅ PyInstaller available")
            print("  ✅ PyInstaller available")
        except ImportError:
            self.issues.append("❌ PyInstaller not installed")
            print("  ❌ PyInstaller not installed")
        
        # Check build script
        build_scripts = ["build.py", "build_optimized.py"]
        found_build_script = False
        for script in build_scripts:
            if Path(script).exists():
                self.successes.append(f"✅ Build script: {script}")
                print(f"  ✅ Build script: {script}")
                found_build_script = True
                break
        
        if not found_build_script:
            self.warnings.append("⚠️ No build script found")
            print("  ⚠️ No build script found")
    
    def generate_report(self):
        """Generate final status report"""
        print("\n" + "="*60)
        print("📊 FINAL STATUS REPORT")
        print("="*60)
        
        print(f"\n✅ SUCCESSES ({len(self.successes)}):")
        for success in self.successes:
            print(f"  {success}")
        
        if self.warnings:
            print(f"\n⚠️ WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  {warning}")
        
        if self.issues:
            print(f"\n❌ CRITICAL ISSUES ({len(self.issues)}):")
            for issue in self.issues:
                print(f"  {issue}")
        
        # Overall status
        print(f"\n🎯 OVERALL STATUS:")
        if not self.issues:
            if not self.warnings:
                print("  🟢 EXCELLENT - Ready for production")
            else:
                print("  🟡 GOOD - Minor issues, ready for development")
        else:
            print("  🔴 NEEDS ATTENTION - Critical issues must be resolved")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if self.issues:
            print("  1. Fix critical issues before building")
            print("  2. Run: pip install -r requirements.txt")
        if self.warnings:
            print("  3. Address warnings for optimal performance")
        if not self.issues and not self.warnings:
            print("  1. Ready to build: python build_optimized.py")
            print("  2. Ready to run: python main.py")
        
        return len(self.issues) == 0

def main():
    """Run comprehensive status check"""
    print("🔍 HKJC Racing Analyzer - Status Check")
    print("="*50)
    
    checker = StatusChecker()
    
    # Run all checks
    checker.check_dependencies()
    checker.check_database()
    checker.check_ui_components()
    checker.check_ml_service()
    checker.check_translations()
    checker.check_main_application()
    checker.check_build_readiness()
    
    # Generate report
    is_healthy = checker.generate_report()
    
    # Exit code
    sys.exit(0 if is_healthy else 1)

if __name__ == "__main__":
    main()