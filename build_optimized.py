#!/usr/bin/env python3
"""
Optimized Build Script for PyQt Racing Analyzer
Handles dependencies and creates a production-ready executable
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_and_install_dependencies():
    """Check and install required dependencies"""
    required_packages = [
        "PyQt5>=5.15.0",
        "pandas>=1.5.0", 
        "numpy>=1.21.0",
        "scikit-learn>=1.1.0",
        "xgboost>=1.6.0",
        "lightgbm>=3.3.0",
        "requests>=2.28.0",
        "beautifulsoup4>=4.11.0",
        "pyinstaller>=5.0.0"
    ]
    
    print("📦 Checking dependencies...")
    missing = []
    
    for package in required_packages:
        pkg_name = package.split(">=")[0].split("==")[0]
        try:
            __import__(pkg_name.replace("-", "_"))
            print(f"  ✅ {pkg_name}")
        except ImportError:
            missing.append(package)
            print(f"  ❌ {pkg_name}")
    
    if missing:
        print(f"\n🔧 Installing missing packages: {', '.join(missing)}")
        subprocess.run([sys.executable, "-m", "pip", "install"] + missing, check=True)
        print("✅ Dependencies installed")
    else:
        print("✅ All dependencies satisfied")

def clean_build_artifacts():
    """Clean previous build artifacts"""
    print("🧹 Cleaning build artifacts...")
    
    artifacts = ["build", "dist", "__pycache__", "*.spec"]
    for pattern in artifacts:
        if pattern.startswith("*"):
            # Handle glob patterns
            import glob
            for file in glob.glob(pattern):
                if os.path.isfile(file):
                    os.remove(file)
                    print(f"  Removed: {file}")
        else:
            path = Path(pattern)
            if path.exists():
                if path.is_dir():
                    shutil.rmtree(path)
                    print(f"  Removed directory: {path}")
                else:
                    path.unlink()
                    print(f"  Removed file: {path}")

def create_executable():
    """Create the executable using PyInstaller"""
    print("🏗️ Building executable...")
    
    # PyInstaller command with optimized settings
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name=HKJC_Racing_Analyzer",
        "--add-data=ui:ui",
        "--add-data=ml:ml", 
        "--add-data=engine:engine",
        "--add-data=database:database",
        "--add-data=i18n:i18n",
        "--hidden-import=PyQt5.QtCore",
        "--hidden-import=PyQt5.QtGui", 
        "--hidden-import=PyQt5.QtWidgets",
        "--hidden-import=sklearn.ensemble",
        "--hidden-import=xgboost",
        "--hidden-import=lightgbm",
        "--hidden-import=pandas",
        "--hidden-import=numpy",
        "--exclude-module=matplotlib",
        "--exclude-module=tkinter",
        "main.py"
    ]
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Build successful!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False

def copy_additional_files():
    """Copy additional required files to dist"""
    print("📋 Copying additional files...")
    
    dist_dir = Path("dist")
    if not dist_dir.exists():
        print("❌ Dist directory not found")
        return False
    
    # Copy database if it exists
    db_file = Path("database/hkjc_races.db")
    if db_file.exists():
        shutil.copy2(db_file, dist_dir / "hkjc_races.db")
        print("  ✅ Database copied")
    
    # Copy models if they exist
    models_dir = Path("../models")
    if models_dir.exists():
        dist_models = dist_dir / "models"
        if dist_models.exists():
            shutil.rmtree(dist_models)
        shutil.copytree(models_dir, dist_models)
        print("  ✅ ML models copied")
    
    # Copy translations
    i18n_dir = Path("i18n")
    if i18n_dir.exists():
        dist_i18n = dist_dir / "i18n"
        if dist_i18n.exists():
            shutil.rmtree(dist_i18n)
        shutil.copytree(i18n_dir, dist_i18n)
        print("  ✅ Translations copied")
    
    return True

def create_installer_info():
    """Create installer information file"""
    info_content = f"""
HKJC Racing Analyzer - Professional Edition
==========================================

Version: 1.0.0
Build Date: {os.popen('date').read().strip()}
Platform: {sys.platform}

Installation:
1. Extract all files to desired location
2. Run HKJC_Racing_Analyzer executable
3. No additional dependencies required

Features:
✅ Native PyQt5 interface
✅ Direct ML model integration  
✅ Real-time race analysis
✅ Professional data visualization
✅ Multi-language support
✅ Single executable deployment

System Requirements:
- macOS 10.14+ / Windows 10+ / Linux
- 4GB RAM minimum
- 500MB disk space

Support: Professional racing analysis platform
"""
    
    with open("dist/README.txt", "w") as f:
        f.write(info_content)
    print("  ✅ Installation info created")

def main():
    """Main build process"""
    print("🚀 HKJC Racing Analyzer - Build Process")
    print("=" * 50)
    
    # Change to script directory
    os.chdir(Path(__file__).parent)
    
    try:
        # Step 1: Dependencies
        check_and_install_dependencies()
        
        # Step 2: Clean
        clean_build_artifacts()
        
        # Step 3: Build
        if not create_executable():
            sys.exit(1)
        
        # Step 4: Copy files
        if not copy_additional_files():
            sys.exit(1)
        
        # Step 5: Create info
        create_installer_info()
        
        print("\n🎉 Build completed successfully!")
        print("\nDistribution files:")
        print("  📁 dist/HKJC_Racing_Analyzer (executable)")
        print("  📁 dist/hkjc_races.db (database)")
        print("  📁 dist/models/ (ML models)")
        print("  📁 dist/i18n/ (translations)")
        print("  📄 dist/README.txt (installation guide)")
        
        # Get file sizes
        exe_path = Path("dist/HKJC_Racing_Analyzer")
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"\n📊 Executable size: {size_mb:.1f} MB")
        
        print("\n✅ Ready for distribution!")
        
    except Exception as e:
        print(f"\n💥 Build failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()