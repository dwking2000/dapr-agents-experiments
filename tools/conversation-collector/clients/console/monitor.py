#!/usr/bin/env python3
"""
Quick launcher for the ConversationCollector Console Monitor.
"""

import os
import sys
import subprocess

def main():
    """Launch the console monitor with proper environment."""
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(script_dir, "app.py")
    
    # Change to the project root to ensure proper imports
    project_root = os.path.join(script_dir, "..", "..", "..", "..")
    os.chdir(project_root)
    
    try:
        # Launch the console app
        subprocess.run([sys.executable, app_path] + sys.argv[1:])
    except KeyboardInterrupt:
        print("\nMonitor stopped.")
    except Exception as e:
        print(f"Error launching monitor: {e}")

if __name__ == "__main__":
    main()