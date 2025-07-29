# 🔐 File Transfer CLI

A **GUI-based secure file transfer tool** for Windows that allows you to effortlessly transfer files and folders to remote servers over SSH using password or key-based authentication.

## ✨ Features

- **🔐 Secure SSH/SFTP Transfer**: Encrypted file transfer using SSH protocol
- **🔑 Dual Authentication**: Support for both password and private key authentication
- **💾 Connection Profiles**: Save and reuse SSH connection settings
- **📦 Smart Archiving**: Automatically creates compressed archives for efficient transfer
- **🖥️ Modern GUI**: Clean, intuitive PyQt5-based interface
- **📁 Multi-Selection**: Transfer multiple files and folders with individual removal
- **🔄 Remote Extraction**: Optional automatic extraction on remote server
- **📊 Real-time Logging**: Live transfer status and progress updates
- **🚀 Single Executable**: No Python installation required on target machines

## 🎯 Use Cases

- **Web Developers**: Upload website files to production servers
- **System Administrators**: Transfer configuration files and backups
- **Content Creators**: Upload media files to remote storage
- **IT Professionals**: Deploy software packages to multiple servers
- **Home Users**: Backup files to remote servers or NAS devices

## 🚀 Quick Start

### Option 1: Run the Executable (Recommended)

1. Download `FileTransferCLI.exe`
2. Double-click to run
3. No installation required!

### Option 2: Build from Source

```bash
# Clone or download the project
cd file_transfer_cli

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py

# Or build executable
python build_exe.py
```

## 📋 Requirements

### For Running the Executable
- **Windows 10/11** (64-bit)
- **No Python installation required**

### For Building from Source
- **Python 3.7+**
- **Windows 10/11** (64-bit)
- **pip** (Python package manager)

## 🛠️ Installation

### Building the Executable

1. **Install Python** (if not already installed)
   ```bash
   # Download from python.org or use winget
   winget install Python.Python.3.11
   ```

2. **Clone/Download the Project**
   ```bash
   git clone <repository-url>
   cd file_transfer_cli
   ```

3. **Build the Executable**
   ```bash
   python build_exe.py
   ```

4. **Find Your Executable**
   - `FileTransferCLI.exe` in the project root
   - Ready to distribute to any Windows machine!

## 📖 Usage Guide

### 1. Connection Profiles

**Save Connection Settings:**
- Fill in your SSH connection details
- Click "Save Current as Profile"
- Enter a profile name (e.g., "Production Server")
- Click OK

**Load Saved Profiles:**
- Select a profile from the dropdown
- All fields will be automatically filled
- Ready to transfer files!

**Manage Profiles:**
- Click "Manage Profiles" to open the profile manager
- Add, edit, delete, or test profiles

### 2. SSH Connection Setup

**Host Configuration:**
- **Host/IP**: Enter the server address (e.g., `192.168.1.100` or `example.com`)
- **Port**: SSH port (default: `22`)
- **Username**: Your SSH username

**Authentication:**
- **Password**: Enter your SSH password
- **Private Key**: Select a `.pem`, `.ppk`, or `.key` file

### 3. File Selection

**Adding Files:**
- Click "📁 Add Files" to select individual files
- Click "📂 Add Folders" to select entire directories
- Use "🗑️ Remove Selected" to remove specific files
- Use "🗑️ Clear All" to remove all selections

**Features:**
- Multiple files and folders can be selected
- Individual file removal with multi-selection
- Visual file type indicators (📄 for files, 📁 for folders)
- File count display

### 4. Remote Configuration

**Destination Path:**
- Enter the remote directory path (e.g., `/home/user/uploads/`)
- Directory will be created automatically if it doesn't exist

**Extraction Options:**
- ✅ **Extract on remote**: Automatically extract the archive
- ❌ **Keep archive**: Leave the compressed file on server

### 5. Transfer Process

1. **Click "🚀 Start Transfer"**
2. **Monitor Progress** in the log window
3. **Wait for Completion** message
4. **Files are ready** on the remote server!

## 🔧 Configuration Examples

### Basic Password Authentication
```
Host: 192.168.1.100
Port: 22
Username: admin
Password: your_password
Remote Path: /home/admin/uploads/
```

### Key-Based Authentication
```
Host: example.com
Port: 22
Username: deploy
Key File: C:\Users\user\.ssh\id_rsa
Remote Path: /var/www/html/
```

### Cloud Server Example
```
Host: ec2-xx-xx-xx-xx.compute-1.amazonaws.com
Port: 22
Username: ubuntu
Key File: C:\path\to\your-key.pem
Remote Path: /home/ubuntu/app/
```

## 🛡️ Security Features

- **🔐 SSH Encryption**: All data is encrypted in transit
- **🔑 Key Authentication**: Support for RSA, DSA, ECDSA keys
- **🛡️ Password Protection**: Secure password handling with encryption
- **📦 Archive Integrity**: Files are compressed and verified
- **🧹 Automatic Cleanup**: Temporary files are removed after transfer
- **💾 Encrypted Profiles**: Connection profiles are securely stored

## 📊 Technical Details

### Architecture
- **GUI Framework**: PyQt5 for modern interface
- **SSH Library**: Paramiko for secure connections
- **Archive Format**: tar.gz for efficient compression
- **Build Tool**: PyInstaller for single executable
- **Profile Storage**: Encrypted JSON with cryptography library

### Transfer Process
1. **Archive Creation**: Files are compressed into tar.gz
2. **SSH Connection**: Secure connection established
3. **SFTP Upload**: Archive transferred via SFTP
4. **Remote Extraction**: Optional automatic extraction
5. **Cleanup**: Temporary files removed

### File Handling
- **Compression**: Automatic tar.gz compression
- **Integrity**: Archive verification before transfer
- **Progress**: Real-time transfer status
- **Error Handling**: Comprehensive error reporting

## 🐛 Troubleshooting

### Common Issues

**Connection Failed:**
- Verify host/IP address and port
- Check firewall settings
- Ensure SSH service is running on server

**Authentication Error:**
- Verify username and password
- Check key file permissions (should be 600)
- Ensure key file is in correct format

**Transfer Failed:**
- Check remote directory permissions
- Verify available disk space
- Ensure network connectivity

**Profile Issues:**
- Profiles are stored in `profiles.json`
- Passwords are encrypted using system-specific keys
- Delete `profiles.json` to reset all profiles

### Debug Mode

Run with console output for detailed logging:
```bash
python main.py --debug
```

## 🔄 Future Enhancements

- **🔄 Resumable Uploads**: Resume interrupted transfers
- **📊 Progress Bars**: Real-time transfer progress
- **🖱️ Drag & Drop**: Direct file drag support
- **🖥️ System Tray**: Background transfer queue
- **🌐 Cross-Platform**: Linux and macOS support

## 🤝 Contributing

We welcome contributions to the File Transfer CLI! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute.

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Test** thoroughly
5. **Submit** a pull request

## 📄 License

This project is licensed under the MIT License with an **attribution requirement** - see the [LICENSE](LICENSE) file for details.

### Attribution Requirements

If you use this code or any part of it in your projects, you must:

1. Include the original copyright notice
2. Provide attribution to the original author (MrBeanDev)
3. Include a link to the original repository: [https://github.com/mrbeandev/File-Transfer-Cli](https://github.com/mrbeandev/File-Transfer-Cli)
4. State any significant changes made to the original code

This attribution should be visible in your project's documentation and source code.

### Using the CREDITS.md Template

We've included a `CREDITS.md` file in the repository that you can copy and include in your project to satisfy the attribution requirements. Modify it as needed to reflect which parts of the code you're using.

## 🙏 Acknowledgments

- **PyQt5**: Modern GUI framework
- **Paramiko**: SSH/SFTP library
- **PyInstaller**: Executable packaging
- **Cryptography**: Secure profile storage
- **Python Community**: Excellent documentation and support

---

**Made with ❤️ for secure file transfers** 