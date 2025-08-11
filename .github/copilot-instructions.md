# Copilot Instructions for File Transfer CLI

## Project Overview
File Transfer CLI is a GUI-based secure file transfer tool built with PyQt5 and Paramiko. It allows users to transfer files and folders to remote servers via SSH/SFTP with password or key-based authentication.

## Architecture

### Core Components
- **GUI Layer (`main.py`)**: PyQt5-based interface with `FileTransferGUI` as the main window class
- **Worker Thread (`FileTransferWorker` in `main.py`)**: Handles file operations in a separate thread to avoid freezing the UI
- **Profile Management (`profile_manager.py`)**: Manages encrypted SSH connection profiles
- **Profile Dialog (`profile_dialog.py`)**: UI for creating/editing connection profiles
- **Build System (`build_exe.py`)**: PyInstaller configuration for creating standalone executables

### Data Flow
1. User inputs SSH credentials and selects files
2. Files are compressed into a temporary tar.gz archive
3. SFTP connection established using Paramiko
4. Archive transferred to remote server
5. Optional automatic extraction on the server
6. Cleanup of temporary files

## Development Workflow

### Build Process
```bash
# Run application in development mode
python main.py

# Build standalone executable (creates dist/FileTransferCLI.exe)
python build_exe.py
```

### GitHub Actions
- Automated Windows builds on push/PR to main branch
- Lint checks with flake8
- Builds executable and uploads as artifact

## Project-Specific Patterns

### Encrypted Profile Storage
- Profiles are stored in `profiles.json` with system-specific encryption
- Use `ProfileManager` class to access/modify profiles securely

### Progress Handling
- Transfer progress is reported via Qt signals (`progress_signal`, `success_signal`, etc.)
- Log messages should be formatted as `[Operation] Message` for consistency

### Error Handling
- Remote operations use try/except with detailed error messages
- Network errors are propagated to the UI via signals

### CI Environment Adaptations
- The `safe_emoji()` function in `build_exe.py` provides ASCII alternatives in CI environments
- Set `CI=true` environment variable when running in automation

## Key Integration Points
- **SSH/SFTP**: Paramiko library handles all remote connections
- **Compression**: Python's built-in tarfile module for archive creation
- **UI Events**: PyQt5 signal/slot mechanism for asynchronous operations
- **Build System**: PyInstaller with custom icon and hidden imports

## Common Patterns
- Modal dialog pattern for configuration screens
- Worker thread pattern for long-running operations
- Signal/slot pattern for UI updates from background threads
- Local-remote file transfer pattern with temporary archives

## Troubleshooting
- Icon conversion requires Pillow library (`pip install pillow`)
- Profile encryption uses system-specific keys; profiles cannot be shared between machines
- Debug mode: `python main.py --debug` shows console output
