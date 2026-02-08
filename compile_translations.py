#!/usr/bin/env python3
"""
Compile Qt translation files (.ts to .qm)
"""

import os
import subprocess
import sys

def compile_translations():
    """Compile all .ts files to .qm files"""
    i18n_dir = os.path.join(os.path.dirname(__file__), 'i18n')
    
    if not os.path.exists(i18n_dir):
        print(f"Error: i18n directory not found: {i18n_dir}")
        return False
    
    ts_files = [f for f in os.listdir(i18n_dir) if f.endswith('.ts')]
    
    if not ts_files:
        print("No .ts files found to compile")
        return False
    
    print(f"Found {len(ts_files)} translation file(s) to compile:")
    
    success_count = 0
    for ts_file in ts_files:
        ts_path = os.path.join(i18n_dir, ts_file)
        qm_file = ts_file.replace('.ts', '.qm')
        qm_path = os.path.join(i18n_dir, qm_file)
        
        print(f"\nCompiling: {ts_file} -> {qm_file}")
        
        try:
            # Try using lrelease (Qt5 tool)
            result = subprocess.run(
                ['lrelease', ts_path, '-qm', qm_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"✓ Successfully compiled {ts_file}")
                success_count += 1
            else:
                print(f"✗ Failed to compile {ts_file}")
                print(f"Error: {result.stderr}")
                
        except FileNotFoundError:
            print("Error: 'lrelease' command not found.")
            print("Please install Qt5 development tools:")
            print("  macOS: brew install qt5")
            print("  Ubuntu: sudo apt-get install qttools5-dev-tools")
            print("  Windows: Install Qt from https://www.qt.io/download")
            return False
    
    print(f"\n{'='*50}")
    print(f"Compilation complete: {success_count}/{len(ts_files)} files compiled successfully")
    return success_count == len(ts_files)

if __name__ == '__main__':
    success = compile_translations()
    sys.exit(0 if success else 1)
