#!/usr/bin/env python3
"""
Build script for creating a single executable file using PyInstaller
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# Detect if we're running in a CI environment (like GitHub Actions)
CI_ENV = os.environ.get('CI', 'false').lower() == 'true'

# Use ASCII alternatives for emojis in CI environments
def safe_emoji(emoji, alt_text):
    """Return the emoji if not in CI, otherwise return an ASCII alternative"""
    if CI_ENV:
        return alt_text
    return emoji


def build_executable():
    """Build the executable using PyInstaller"""

    print(f"{safe_emoji('🔨', '[BUILD]')} Building File Transfer CLI executable...")

    # Clean previous builds
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("file_transfer_gui.spec"):
        os.remove("file_transfer_gui.spec")

    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",  # Single executable
        "--windowed",  # No console window
        "--name=FileTransferCLI",  # Executable name
        "--icon=logo.png",  # Icon (if exists)
        "--add-data=README.md;.",  # Include README
        "--hidden-import=paramiko",  # Ensure paramiko is included
        "--hidden-import=PyQt5",
        "--hidden-import=PyQt5.QtCore",
        "--hidden-import=PyQt5.QtWidgets",
        "--hidden-import=PyQt5.QtGui",
        "main.py",
    ]

    # Remove icon parameter if icon doesn't exist
    if not os.path.exists("logo.png"):
        cmd = [arg for arg in cmd if arg != "--icon=logo.png"]

    # Remove README parameter if it doesn't exist
    if not os.path.exists("README.md"):
        cmd = [arg for arg in cmd if arg != "--add-data=README.md;."]

    try:
        # Run PyInstaller
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"{safe_emoji('✅', '[SUCCESS]')} Build completed successfully!")

        # Check if executable was created
        exe_path = "dist/FileTransferCLI.exe"
        if os.path.exists(exe_path):
            file_size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
            print(f"{safe_emoji('📦', '[INFO]')} Executable created: {exe_path}")
            print(f"{safe_emoji('📏', '[INFO]')} File size: {file_size:.1f} MB")

            # Copy to root directory for easy access
            shutil.copy2(exe_path, "FileTransferCLI.exe")
            print(f"{safe_emoji('📋', '[INFO]')} Copied executable to root directory: FileTransferCLI.exe")

        else:
            print(f"{safe_emoji('❌', '[ERROR]')} Executable not found in dist directory")
            return False

    except subprocess.CalledProcessError as e:
        print(f"{safe_emoji('❌', '[ERROR]')} Build failed with error: {e}")
        print(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        print(f"{safe_emoji('❌', '[ERROR]')} Unexpected error during build: {e}")
        return False

    return True


def install_dependencies():
    """Install required dependencies"""
    print(f"{safe_emoji('📦', '[INSTALL]')} Installing dependencies...")

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True,
            capture_output=True,
            text=True,
        )
        print(f"{safe_emoji('✅', '[SUCCESS]')} Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{safe_emoji('❌', '[ERROR]')} Failed to install dependencies: {e}")
        print(f"Error output: {e.stderr}")
        return False


def main():
    """Main build process"""
    print(f"{safe_emoji('🚀', '[START]')} Starting build process for File Transfer CLI")
    print("=" * 60)

    # Check if main file exists
    if not os.path.exists("main.py"):
        print(f"{safe_emoji('❌', '[ERROR]')} main.py not found!")
        return False

    # Install dependencies
    if not install_dependencies():
        return False

    # Build executable
    if not build_executable():
        return False

    print(f"\n{safe_emoji('🎉', '[COMPLETE]')} Build process completed successfully!")
    print(f"{safe_emoji('📁', '[INFO]')} Your executable is ready: FileTransferCLI.exe")
    print(f"\n{safe_emoji('💡', '[TIP]')} Usage:")
    print("   - Double-click FileTransferCLI.exe to run")
    print("   - No Python installation required on target machine")
    print("   - All dependencies are bundled in the executable")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
