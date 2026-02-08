#!/usr/bin/env python3
"""
Build script for HKJC Racing Intelligence Terminal
Creates a standalone executable using PyInstaller
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def print_step(message):
    """Print a formatted step message"""
    print(f"\n{'='*60}")
    print(f"  {message}")
    print(f"{'='*60}\n")


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}\n")
    
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {description} failed!")
        print(f"Return code: {e.returncode}")
        print(f"STDOUT:\n{e.stdout}")
        print(f"STDERR:\n{e.stderr}")
        return False


def clean_build_dirs():
    """Clean previous build directories"""
    print_step("Cleaning previous build directories")
    
    dirs_to_clean = ['build', 'dist']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Removing {dir_name}/...")
            shutil.rmtree(dir_name)
            print(f"✓ Removed {dir_name}/")
        else:
            print(f"✓ {dir_name}/ doesn't exist, skipping")


def check_dependencies():
    """Check if required dependencies are installed"""
    print_step("Checking dependencies")
    
    # Map package names to their import names
    required_packages = {
        'PyInstaller': 'PyInstaller',
        'PyQt5': 'PyQt5.QtCore',
        'pandas': 'pandas',
        'numpy': 'numpy',
        'scikit-learn': 'sklearn'
    }
    missing_packages = []
    
    for package, import_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"✓ {package} is installed")
        except ImportError:
            print(f"✗ {package} is NOT installed")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Please install them using: pip install -r requirements.txt")
        return False
    
    return True


def build_executable():
    """Build the executable using PyInstaller"""
    print_step("Building executable with PyInstaller")
    
    # PyInstaller command
    command = [
        sys.executable,
        '-m',
        'PyInstaller',
        '--clean',
        '--noconfirm',
        'hkjc_racing_analyzer.spec'
    ]
    
    success = run_command(command, "PyInstaller build")
    
    if success:
        print("\n✓ Build completed successfully!")
        return True
    else:
        print("\n✗ Build failed!")
        return False


def verify_build():
    """Verify the build output"""
    print_step("Verifying build output")
    
    exe_name = 'HKJC_Racing_Analyzer'
    
    if sys.platform == 'win32':
        exe_path = os.path.join('dist', f'{exe_name}.exe')
    elif sys.platform == 'darwin':
        exe_path = os.path.join('dist', exe_name)
    else:
        exe_path = os.path.join('dist', exe_name)
    
    if os.path.exists(exe_path):
        file_size = os.path.getsize(exe_path)
        size_mb = file_size / (1024 * 1024)
        print(f"✓ Executable created: {exe_path}")
        print(f"✓ File size: {size_mb:.2f} MB")
        return True
    else:
        print(f"✗ Executable not found at: {exe_path}")
        return False


def create_readme():
    """Create a README for the distribution"""
    print_step("Creating distribution README")
    
    readme_content = """# HKJC Racing Intelligence Terminal

## Installation

No installation required! This is a standalone executable.

## Usage

Simply double-click the executable to launch the application.

### Windows
- Double-click `HKJC_Racing_Analyzer.exe`

### macOS
- Double-click `HKJC_Racing_Analyzer`
- If you get a security warning, right-click and select "Open"

### Linux
- Run `./HKJC_Racing_Analyzer` from terminal

## Features

- Real-time race data analysis
- Machine learning predictions
- Interactive dashboard
- Database browser
- Model retraining capabilities

## Data

The application will automatically create and manage its database files in the same directory.

## Troubleshooting

If the application fails to start:
1. Ensure you have sufficient disk space
2. Check that no antivirus is blocking the executable
3. Run from terminal/command prompt to see error messages

## Support

For issues or questions, please contact the development team.
"""
    
    readme_path = os.path.join('dist', 'README.txt')
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"✓ Created README at: {readme_path}")


def main():
    """Main build process"""
    print("\n" + "="*60)
    print("  HKJC Racing Intelligence Terminal - Build Script")
    print("="*60)
    
    # Step 1: Check dependencies
    if not check_dependencies():
        print("\n✗ Dependency check failed. Exiting.")
        sys.exit(1)
    
    # Step 2: Clean previous builds
    clean_build_dirs()
    
    # Step 3: Build executable
    if not build_executable():
        print("\n✗ Build failed. Exiting.")
        sys.exit(1)
    
    # Step 4: Verify build
    if not verify_build():
        print("\n✗ Build verification failed. Exiting.")
        sys.exit(1)
    
    # Step 5: Create distribution README
    create_readme()
    
    # Success!
    print_step("Build completed successfully!")
    print("\nYour executable is ready in the 'dist' directory.")
    print("You can now distribute the executable to users.\n")


if __name__ == '__main__':
    main()
