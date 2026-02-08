import os
import subprocess
import sys

def compile_ts():
    ts_file = "zh_HK.ts"
    qm_file = "zh_HK.qm"
    
    # Try to find lrelease
    commands = ["lrelease", "lrelease-qt5", "lrelease5"]
    
    success = False
    for cmd in commands:
        try:
            print(f"Trying to use {cmd}...")
            subprocess.run([cmd, ts_file, "-qm", qm_file], check=True)
            print(f"Successfully compiled {ts_file} to {qm_file}")
            success = True
            break
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
            
    if not success:
        print("\nError: Could not find 'lrelease' command.")
        print("Please ensure you have Qt Tools installed.")
        print("On macOS: brew install qt")
        print("On Ubuntu/Debian: sudo apt-get install qttools5-dev-tools")
        print("\nAlternatively, you can open the .ts file in Qt Linguist and use File -> Release.")
        sys.exit(1)

if __name__ == "__main__":
    # Change to the script's directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    compile_ts()
