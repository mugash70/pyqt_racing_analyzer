#!/usr/bin/env python3
"""
Build script for PyQt Racing Analyzer
Creates a single executable using PyInstaller
"""

import os
import sys
import subprocess
from pathlib import Path

def build_executable():
    """Build standalone executable with PyInstaller"""

    print("🏗️  Building PyQt Racing Analyzer executable...")

    # Ensure we're in the right directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",                    # Single executable file
        "--windowed",                  # No console window (on Windows)
        "--name=HKJC_Race_Analysis",   # Executable name
        "--icon=icon.ico",             # Icon (if available)
        "--add-data=ml:ml",            # Include ML module
        "--add-data=ui:ui",            # Include UI module
        "--hidden-import=PyQt5.QtCore",
        "--hidden-import=PyQt5.QtGui",
        "--hidden-import=PyQt5.QtWidgets",
        "--hidden-import=sklearn",
        "--hidden-import=sklearn.ensemble",
        "--hidden-import=sklearn.preprocessing",
        "--hidden-import=xgboost",
        "--hidden-import=lightgbm",
        "--hidden-import=pandas",
        "--hidden-import=numpy",
        "--hidden-import=sqlite3",
        "--hidden-import=requests",
        "--hidden-import=beautifulsoup4",
        "--hidden-import=selenium",
        "--hidden-import=webdriver_manager",
        "main.py"                      # Main script
    ]

    print(f"Running: {' '.join(cmd)}")

    try:
        # Run PyInstaller
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)

        print("✅ Build successful!")
        print("📁 Executable created in: dist/HKJC_Race_Analysis")

        # Copy additional files
        dist_dir = script_dir / "dist"
        if dist_dir.exists():
            # Copy model files if they exist
            models_dir = script_dir.parent / "models"
            if models_dir.exists():
                import shutil
                shutil.copytree(models_dir, dist_dir / "models", dirs_exist_ok=True)
                print("📋 Copied ML models to dist/")

            # Copy database if it exists
            db_file = script_dir.parent / "hkjc_races.db"
            if db_file.exists():
                shutil.copy2(db_file, dist_dir / "hkjc_races.db")
                print("💾 Copied race database to dist/")

        print("\n🎉 Ready to distribute!")
        print("   - Single executable: dist/HKJC_Race_Analysis")
        print("   - No dependencies required on target machine")
        print("   - Includes ML models and race data")

    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False

    return True

def clean_build():
    """Clean previous build artifacts"""
    print("🧹 Cleaning previous build...")

    dirs_to_clean = ["build", "dist", "*.spec"]

    for item in dirs_to_clean:
        path = Path(item)
        if path.exists():
            if path.is_dir():
                import shutil
                shutil.rmtree(path)
                print(f"   Removed directory: {path}")
            else:
                path.unlink()
                print(f"   Removed file: {path}")

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        "PyQt5", "pandas", "numpy", "scikit-learn",
        "xgboost", "lightgbm", "pyinstaller"
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print("⚠️  Missing required packages:")
        for pkg in missing_packages:
            print(f"   - {pkg}")
        print("\nInstall with: pip install " + " ".join(missing_packages))
        return False

    print("✅ All dependencies installed")
    return True

if __name__ == "__main__":
    print("🚀 PyQt Racing Analyzer Build Script")
    print("=" * 40)

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Clean previous build
    clean_build()

    # Build executable
    if build_executable():
        print("\n🎊 Build completed successfully!")
        print("\nTo run the application:")
        print("   ./dist/HKJC_Race_Analysis")
    else:
        print("\n💥 Build failed!")
        sys.exit(1)