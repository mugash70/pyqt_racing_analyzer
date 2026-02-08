#!/usr/bin/env python3
"""
Generate .qm file from .ts file using Qt's lrelease tool
"""

import os
import subprocess
import sys

def compile_translations():
    """Compile .ts files to .qm using lrelease"""
    i18n_dir = os.path.join(os.path.dirname(__file__), 'i18n')
    ts_file = os.path.join(i18n_dir, 'zh_HK.ts')
    qm_file = os.path.join(i18n_dir, 'zh_HK.qm')
    
    print("="*60)
    print("Qt Translation Compiler")
    print("="*60)
    print()
    
    if not os.path.exists(ts_file):
        print(f"✗ Error: {ts_file} not found")
        return False
    
    # Try to find lrelease
    lrelease_paths = [
        '/opt/homebrew/opt/qt@5/bin/lrelease',  # macOS Homebrew
        '/usr/local/opt/qt@5/bin/lrelease',
        'lrelease',  # In PATH
        'lrelease-qt5'
    ]
    
    lrelease = None
    for path in lrelease_paths:
        try:
            result = subprocess.run([path, '-version'], 
                                  capture_output=True, timeout=2)
            if result.returncode == 0:
                lrelease = path
                print(f"✓ Found lrelease: {path}")
                break
        except:
            continue
    
    if not lrelease:
        print("✗ lrelease not found")
        print("\nInstall Qt5 tools:")
        print("  macOS: brew install qt@5")
        print("  Ubuntu: sudo apt-get install qttools5-dev-tools")
        return False
    
    # Compile
    print(f"\nCompiling: {ts_file}")
    result = subprocess.run(
        [lrelease, ts_file, '-qm', qm_file],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        size = os.path.getsize(qm_file)
        print(f"✓ Successfully created {qm_file} ({size} bytes)")
        print(result.stdout)
        print("\n" + "="*60)
        print("Translation compilation complete!")
        print("="*60)
        return True
    else:
        print(f"✗ Compilation failed")
        print(result.stderr)
        return False

if __name__ == '__main__':
    success = compile_translations()
    sys.exit(0 if success else 1)
