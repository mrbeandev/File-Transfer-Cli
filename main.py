import sys
import os
import tarfile
import tempfile
import uuid
import threading
from datetime import datetime
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QPushButton,
    QTextEdit,
    QFileDialog,
    QListWidget,
    QRadioButton,
    QButtonGroup,
    QCheckBox,
    QProgressBar,
    QMessageBox,
    QGroupBox,
    QComboBox,
    QListWidgetItem,
    QSplitter,
    QFrame,
    QInputDialog,
    QSplashScreen,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPainter

import paramiko

# Import our custom modules
from profile_manager import ProfileManager
from profile_dialog import ProfileDialog


class LoadingScreen(QSplashScreen):
    """Loading screen with animation"""

    def __init__(self):
        # Load the logo for the splash screen
        logo_pixmap = QPixmap("logo.png")

        # Scale the logo to a larger size (e.g., 400x400)
        scaled_logo = logo_pixmap.scaled(
            400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )

        # Create a transparent pixmap for the splash screen
        pixmap = QPixmap(500, 450)
        pixmap.fill(Qt.transparent)

        # Create a painter to draw on the pixmap
        painter = QPainter(pixmap)

        # Calculate the center position for the scaled logo
        logo_x = (pixmap.width() - scaled_logo.width()) // 2
        logo_y = 20  # Position from top

        # Draw the scaled logo
        painter.drawPixmap(logo_x, logo_y, scaled_logo)
        painter.end()

        super().__init__(pixmap)
        self.setWindowTitle("Loading File Transfer CLI...")

        # Set window flags
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)


class FileTransferWorker(QThread):
    """Worker thread for handling file transfer operations"""

    progress_signal = pyqtSignal(str)
    progress_update_signal = pyqtSignal(int, int)  # current, total bytes
    error_signal = pyqtSignal(str)
    success_signal = pyqtSignal()

    def __init__(self, ssh_config, files_to_transfer, remote_path, extract_archive):
        super().__init__()
        self.ssh_config = ssh_config
        self.files_to_transfer = files_to_transfer
        self.remote_path = remote_path
        self.extract_archive = extract_archive
        self.uploaded_archive_name = None
        self.archive_size = 0

    def run(self):
        try:
            # Create temporary archive
            self.progress_signal.emit("Creating archive...")
            temp_archive = self._create_archive()

            # Get archive size
            self.archive_size = os.path.getsize(temp_archive)
            self.progress_signal.emit(
                f"Archive created: {self._format_size(self.archive_size)}"
            )

            # Upload file with progress
            self.progress_signal.emit("Preparing to upload archive...")
            self._upload_file_with_progress(temp_archive)

            # Extract if requested
            if self.extract_archive:
                self.progress_signal.emit("Extracting archive on remote server...")
                self._extract_archive()

            # Cleanup
            self.progress_signal.emit("Cleaning up...")
            os.remove(temp_archive)

            self.success_signal.emit()

        except Exception as e:
            self.error_signal.emit(str(e))

    def _format_size(self, size_bytes):
        """Format bytes to human readable size"""
        if size_bytes == 0:
            return "0 B"

        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1

        return f"{size_bytes:.1f} {size_names[i]}"

    def _create_archive(self):
        """Create a tar.gz archive of selected files"""
        temp_dir = tempfile.gettempdir()
        archive_name = f"file_transfer_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.tar.gz"
        archive_path = os.path.join(temp_dir, archive_name)

        with tarfile.open(archive_path, "w:gz") as tar:
            for file_path in self.files_to_transfer:
                if os.path.exists(file_path):
                    tar.add(file_path, arcname=os.path.basename(file_path))

        return archive_path

    def _upload_file_with_progress(self, local_file):
        """Upload file to remote server via SFTP with progress tracking"""
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            # Connect to SSH server
            if self.ssh_config["auth_method"] == "password":
                ssh.connect(
                    self.ssh_config["host"],
                    port=self.ssh_config["port"],
                    username=self.ssh_config["username"],
                    password=self.ssh_config["password"],
                )
            else:  # key-based authentication
                ssh.connect(
                    self.ssh_config["host"],
                    port=self.ssh_config["port"],
                    username=self.ssh_config["username"],
                    key_filename=self.ssh_config["key_file"],
                )

            # Create SFTP client
            sftp = ssh.open_sftp()

            # Ensure remote directory exists
            try:
                sftp.stat(self.remote_path)
            except FileNotFoundError:
                # Create directory recursively
                ssh.exec_command(f'mkdir -p "{self.remote_path}"')

            # Upload file with progress callback
            remote_file = os.path.join(self.remote_path, os.path.basename(local_file))

            # Custom progress callback
            def progress_callback(transferred, to_be_transferred):
                if to_be_transferred > 0:
                    # Just update the progress bar without logging every step
                    self.progress_update_signal.emit(transferred, to_be_transferred)
                    # Only emit the completion message when done
                    if transferred >= to_be_transferred - 1:
                        self.progress_signal.emit(
                            f"Upload completed: {self._format_size(transferred)} transferred"
                        )

            sftp.put(local_file, remote_file, callback=progress_callback)
            self.uploaded_archive_name = os.path.basename(local_file)

            sftp.close()
            ssh.close()

        except Exception as e:
            ssh.close()
            raise e

    def _extract_archive(self):
        """Extract archive on remote server"""
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            # Connect to SSH server
            if self.ssh_config["auth_method"] == "password":
                ssh.connect(
                    self.ssh_config["host"],
                    port=self.ssh_config["port"],
                    username=self.ssh_config["username"],
                    password=self.ssh_config["password"],
                )
            else:  # key-based authentication
                ssh.connect(
                    self.ssh_config["host"],
                    port=self.ssh_config["port"],
                    username=self.ssh_config["username"],
                    key_filename=self.ssh_config["key_file"],
                )

            # Use the uploaded archive name
            if not self.uploaded_archive_name:
                raise Exception("No archive name available for extraction")

            # Extract the archive and remove it
            extract_cmd = f'cd "{self.remote_path}" && tar -xzf "{self.uploaded_archive_name}" && rm "{self.uploaded_archive_name}"'
            stdin, stdout, stderr = ssh.exec_command(extract_cmd)

            # Wait for command to complete and check for errors
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                error_output = stderr.read().decode()
                raise Exception(
                    f"Extraction failed with exit code {exit_status}: {error_output}"
                )

            ssh.close()

        except Exception as e:
            ssh.close()
            raise e


class FileTransferGUI(QMainWindow):
    """Main GUI window for file transfer application with profile management"""

    def __init__(self):
        super().__init__()
        self.files_to_transfer = []
        self.profile_manager = ProfileManager()
        self.init_ui()
        self.load_last_profile()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("File Transfer CLI v2.0")
        self.setGeometry(100, 100, 1000, 700)

        # Set application icon if logo.png exists
        if os.path.exists("logo.png"):
            self.setWindowIcon(QIcon("logo.png"))

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Profile Management Section
        profile_group = QGroupBox("Connection Profile")
        profile_layout = QHBoxLayout(profile_group)

        profile_layout.addWidget(QLabel("Profile:"))
        self.profile_combo = QComboBox()
        self.profile_combo.addItem("Select Profile...")
        self.profile_combo.currentTextChanged.connect(self.on_profile_changed)
        profile_layout.addWidget(self.profile_combo)

        self.manage_profiles_btn = QPushButton("Manage Profiles")
        self.manage_profiles_btn.clicked.connect(self.show_profile_manager)
        profile_layout.addWidget(self.manage_profiles_btn)

        self.save_current_btn = QPushButton("Save Current as Profile")
        self.save_current_btn.clicked.connect(self.save_current_as_profile)
        profile_layout.addWidget(self.save_current_btn)

        main_layout.addWidget(profile_group)

        # Create splitter for better layout
        splitter = QSplitter(Qt.Horizontal)

        # Left side - Connection and File Selection
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # SSH Configuration Group
        ssh_group = QGroupBox("SSH Connection Configuration")
        ssh_layout = QGridLayout(ssh_group)

        # Host configuration
        ssh_layout.addWidget(QLabel("Host/IP:"), 0, 0)
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("192.168.1.100 or example.com")
        ssh_layout.addWidget(self.host_input, 0, 1)

        ssh_layout.addWidget(QLabel("Port:"), 0, 2)
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(22)
        ssh_layout.addWidget(self.port_input, 0, 3)

        ssh_layout.addWidget(QLabel("Username:"), 1, 0)
        self.username_input = QLineEdit()
        ssh_layout.addWidget(self.username_input, 1, 1, 1, 3)

        # Authentication method
        ssh_layout.addWidget(QLabel("Authentication:"), 2, 0)
        self.auth_group = QButtonGroup()

        self.password_radio = QRadioButton("Password")
        self.password_radio.setChecked(True)
        self.auth_group.addButton(self.password_radio)
        ssh_layout.addWidget(self.password_radio, 2, 1)

        self.key_radio = QRadioButton("Private Key")
        self.auth_group.addButton(self.key_radio)
        ssh_layout.addWidget(self.key_radio, 2, 2)

        # Password input
        ssh_layout.addWidget(QLabel("Password:"), 3, 0)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        ssh_layout.addWidget(self.password_input, 3, 1, 1, 3)

        # Key file input
        ssh_layout.addWidget(QLabel("Key File:"), 4, 0)
        self.key_file_input = QLineEdit()
        self.key_file_input.setEnabled(False)
        ssh_layout.addWidget(self.key_file_input, 4, 1)

        self.browse_key_btn = QPushButton("Browse")
        self.browse_key_btn.setEnabled(False)
        self.browse_key_btn.clicked.connect(self.browse_key_file)
        ssh_layout.addWidget(self.browse_key_btn, 4, 2)

        left_layout.addWidget(ssh_group)

        # File Selection Group with improved UI
        file_group = QGroupBox("File Selection")
        file_layout = QVBoxLayout(file_group)

        # File selection buttons
        btn_layout = QHBoxLayout()
        self.add_files_btn = QPushButton("📁 Add Files")
        self.add_files_btn.clicked.connect(self.add_files)
        btn_layout.addWidget(self.add_files_btn)

        self.add_folders_btn = QPushButton("📂 Add Folders")
        self.add_folders_btn.clicked.connect(self.add_folders)
        btn_layout.addWidget(self.add_folders_btn)

        self.remove_selected_btn = QPushButton("🗑️ Remove Selected")
        self.remove_selected_btn.clicked.connect(self.remove_selected_files)
        btn_layout.addWidget(self.remove_selected_btn)

        self.clear_files_btn = QPushButton("🗑️ Clear All")
        self.clear_files_btn.clicked.connect(self.clear_files)
        btn_layout.addWidget(self.clear_files_btn)

        file_layout.addLayout(btn_layout)

        # File list with checkboxes
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.MultiSelection)
        file_layout.addWidget(self.file_list)

        # File count and size label
        self.file_info_label = QLabel("No files selected")
        file_layout.addWidget(self.file_info_label)

        left_layout.addWidget(file_group)

        # Remote Configuration Group
        remote_group = QGroupBox("Remote Configuration")
        remote_layout = QGridLayout(remote_group)

        remote_layout.addWidget(QLabel("Remote Path:"), 0, 0)
        self.remote_path_input = QLineEdit()
        self.remote_path_input.setPlaceholderText("/home/user/uploads/")
        remote_layout.addWidget(self.remote_path_input, 0, 1)

        self.extract_checkbox = QCheckBox("Extract archive on remote server")
        self.extract_checkbox.setChecked(True)
        remote_layout.addWidget(self.extract_checkbox, 1, 0, 1, 2)

        left_layout.addWidget(remote_group)

        # Transfer controls
        transfer_layout = QHBoxLayout()

        self.transfer_btn = QPushButton("🚀 Start Transfer")
        self.transfer_btn.setStyleSheet(
            "QPushButton { font-weight: bold; font-size: 14px; }"
        )
        self.transfer_btn.clicked.connect(self.start_transfer)
        transfer_layout.addWidget(self.transfer_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        transfer_layout.addWidget(self.progress_bar)

        left_layout.addLayout(transfer_layout)

        # Add left widget to splitter
        splitter.addWidget(left_widget)

        # Right side - Log Output
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # Log output
        log_group = QGroupBox("Transfer Log")
        log_layout = QVBoxLayout(log_group)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        log_layout.addWidget(self.log_output)

        right_layout.addWidget(log_group)

        # Add right widget to splitter
        splitter.addWidget(right_widget)

        # Set splitter proportions
        splitter.setSizes([600, 400])

        main_layout.addWidget(splitter)

        # Connect authentication radio buttons
        self.password_radio.toggled.connect(self.on_auth_method_changed)
        self.key_radio.toggled.connect(self.on_auth_method_changed)

        # Set up worker thread
        self.worker_thread = None

        # Load profiles into combo box
        self.load_profiles()

    def load_profiles(self):
        """Load profiles into the combo box"""
        self.profile_combo.clear()
        self.profile_combo.addItem("Select Profile...")

        profile_names = self.profile_manager.get_profile_names()
        for name in profile_names:
            self.profile_combo.addItem(name)

    def load_last_profile(self):
        """Load the last used profile if available"""
        # For now, just load the first profile if available
        profile_names = self.profile_manager.get_profile_names()
        if profile_names:
            self.profile_combo.setCurrentText(profile_names[0])

    def on_profile_changed(self, profile_name):
        """Handle profile selection change"""
        if profile_name == "Select Profile..." or not profile_name:
            return

        profile_data = self.profile_manager.get_profile(profile_name)
        if profile_data:
            # Fill the form with profile data
            self.host_input.setText(profile_data.get("host", ""))
            self.port_input.setValue(profile_data.get("port", 22))
            self.username_input.setText(profile_data.get("username", ""))
            self.remote_path_input.setText(profile_data.get("remote_path", ""))

            # Set authentication method
            auth_method = profile_data.get("auth_method", "password")
            if auth_method == "password":
                self.password_radio.setChecked(True)
                self.password_input.setText(profile_data.get("password", ""))
            else:
                self.key_radio.setChecked(True)
                self.key_file_input.setText(profile_data.get("key_file", ""))

    def show_profile_manager(self):
        """Show the profile management dialog"""
        dialog = ProfileDialog(self.profile_manager, self)
        dialog.profile_selected.connect(self.load_profile_data)
        dialog.exec_()
        self.load_profiles()

    def load_profile_data(self, profile_data):
        """Load profile data from dialog"""
        self.host_input.setText(profile_data.get("host", ""))
        self.port_input.setValue(profile_data.get("port", 22))
        self.username_input.setText(profile_data.get("username", ""))
        self.remote_path_input.setText(profile_data.get("remote_path", ""))

        # Set authentication method
        auth_method = profile_data.get("auth_method", "password")
        if auth_method == "password":
            self.password_radio.setChecked(True)
            self.password_input.setText(profile_data.get("password", ""))
        else:
            self.key_radio.setChecked(True)
            self.key_file_input.setText(profile_data.get("key_file", ""))

    def save_current_as_profile(self):
        """Save current settings as a new profile"""
        profile_name, ok = QInputDialog.getText(
            self, "Save Profile", "Enter profile name:"
        )

        if ok and profile_name.strip():
            # Collect current settings
            profile_data = {
                "host": self.host_input.text().strip(),
                "port": self.port_input.value(),
                "username": self.username_input.text().strip(),
                "remote_path": self.remote_path_input.text().strip(),
                "auth_method": "password" if self.password_radio.isChecked() else "key",
            }

            if profile_data["auth_method"] == "password":
                profile_data["password"] = self.password_input.text()
            else:
                profile_data["key_file"] = self.key_file_input.text().strip()

            # Save profile
            self.profile_manager.save_profile(profile_name.strip(), profile_data)
            self.load_profiles()

            QMessageBox.information(
                self, "Success", f"Profile '{profile_name}' saved successfully!"
            )

    def on_auth_method_changed(self):
        """Handle authentication method change"""
        if self.password_radio.isChecked():
            self.password_input.setEnabled(True)
            self.key_file_input.setEnabled(False)
            self.browse_key_btn.setEnabled(False)
        else:
            self.password_input.setEnabled(False)
            self.key_file_input.setEnabled(True)
            self.browse_key_btn.setEnabled(True)

    def browse_key_file(self):
        """Browse for private key file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Private Key File",
            "",
            "Key Files (*.pem *.ppk *.key);;All Files (*)",
        )
        if file_path:
            self.key_file_input.setText(file_path)

    def calculate_file_size(self, path):
        """Calculate total size of a file or directory"""
        if os.path.isfile(path):
            return os.path.getsize(path)
        elif os.path.isdir(path):
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.isfile(filepath):
                        total_size += os.path.getsize(filepath)
            return total_size
        return 0

    def format_size(self, size_bytes):
        """Format bytes to human readable size"""
        if size_bytes == 0:
            return "0 B"

        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1

        return f"{size_bytes:.1f} {size_names[i]}"

    def add_files(self):
        """Add files to transfer list"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Files to Transfer", "", "All Files (*)"
        )
        for file_path in files:
            if file_path not in self.files_to_transfer:
                self.files_to_transfer.append(file_path)
                item = QListWidgetItem(f"📄 {os.path.basename(file_path)}")
                item.setData(Qt.UserRole, file_path)
                self.file_list.addItem(item)
        self.update_file_info()

    def add_folders(self):
        """Add folders to transfer list"""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Transfer")
        if folder and folder not in self.files_to_transfer:
            self.files_to_transfer.append(folder)
            item = QListWidgetItem(f"📁 {os.path.basename(folder)}")
            item.setData(Qt.UserRole, folder)
            self.file_list.addItem(item)
        self.update_file_info()

    def remove_selected_files(self):
        """Remove selected files from the list"""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Info", "Please select files to remove.")
            return

        for item in selected_items:
            file_path = item.data(Qt.UserRole)
            if file_path in self.files_to_transfer:
                self.files_to_transfer.remove(file_path)
            self.file_list.takeItem(self.file_list.row(item))

        self.update_file_info()

    def clear_files(self):
        """Clear all files from transfer list"""
        self.files_to_transfer.clear()
        self.file_list.clear()
        self.update_file_info()

    def update_file_info(self):
        """Update the file count and size label"""
        count = len(self.files_to_transfer)
        total_size = 0

        for file_path in self.files_to_transfer:
            total_size += self.calculate_file_size(file_path)

        if count == 0:
            self.file_info_label.setText("No files selected")
        elif count == 1:
            self.file_info_label.setText(
                f"1 file selected • {self.format_size(total_size)}"
            )
        else:
            self.file_info_label.setText(
                f"{count} files selected • {self.format_size(total_size)}"
            )

    def log_message(self, message):
        """Add message to log output"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_output.append(f"[{timestamp}] {message}")
        self.log_output.ensureCursorVisible()

    def validate_inputs(self):
        """Validate all input fields"""
        if not self.host_input.text().strip():
            QMessageBox.warning(
                self, "Validation Error", "Please enter a host/IP address."
            )
            return False

        if not self.username_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter a username.")
            return False

        if self.password_radio.isChecked():
            if not self.password_input.text():
                QMessageBox.warning(
                    self, "Validation Error", "Please enter a password."
                )
                return False
        else:
            if not self.key_file_input.text().strip():
                QMessageBox.warning(
                    self, "Validation Error", "Please select a private key file."
                )
                return False
            if not os.path.exists(self.key_file_input.text()):
                QMessageBox.warning(
                    self, "Validation Error", "Selected key file does not exist."
                )
                return False

        if not self.files_to_transfer:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please select at least one file or folder to transfer.",
            )
            return False

        if not self.remote_path_input.text().strip():
            QMessageBox.warning(
                self, "Validation Error", "Please enter a remote destination path."
            )
            return False

        return True

    def start_transfer(self):
        """Start the file transfer process"""
        if not self.validate_inputs():
            return

        # Prepare SSH configuration
        ssh_config = {
            "host": self.host_input.text().strip(),
            "port": self.port_input.value(),
            "username": self.username_input.text().strip(),
            "auth_method": "password" if self.password_radio.isChecked() else "key",
        }

        if ssh_config["auth_method"] == "password":
            ssh_config["password"] = self.password_input.text()
        else:
            ssh_config["key_file"] = self.key_file_input.text().strip()

        # Disable UI during transfer
        self.transfer_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        # Clear log
        self.log_output.clear()
        self.log_message("Starting file transfer...")

        # Create and start worker thread
        self.worker_thread = FileTransferWorker(
            ssh_config,
            self.files_to_transfer,
            self.remote_path_input.text().strip(),
            self.extract_checkbox.isChecked(),
        )

        self.worker_thread.progress_signal.connect(self.log_message)
        self.worker_thread.progress_update_signal.connect(self.update_progress)
        self.worker_thread.error_signal.connect(self.on_transfer_error)
        self.worker_thread.success_signal.connect(self.on_transfer_success)
        self.worker_thread.finished.connect(self.on_transfer_finished)

        self.worker_thread.start()

    def update_progress(self, current_bytes, total_bytes):
        """Update progress bar during upload"""
        if total_bytes > 0:
            progress_percent = int((current_bytes / total_bytes) * 100)
            self.progress_bar.setValue(progress_percent)

    def on_transfer_success(self):
        """Handle successful transfer"""
        self.log_message("Transfer completed successfully!")
        QMessageBox.information(
            self, "Success", "File transfer completed successfully!"
        )

    def on_transfer_error(self, error_message):
        """Handle transfer error"""
        self.log_message(f"Error: {error_message}")
        QMessageBox.critical(
            self, "Transfer Error", f"Transfer failed: {error_message}"
        )

    def on_transfer_finished(self):
        """Handle transfer completion"""
        self.transfer_btn.setEnabled(True)
        self.progress_bar.setVisible(False)


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("File Transfer CLI v2.0")

    # Set application style
    app.setStyle("Fusion")

    # Show loading screen
    splash = LoadingScreen()
    splash.show()

    # Process events to show splash screen
    app.processEvents()

    # Create main window
    window = FileTransferGUI()

    # Simulate loading time (remove this in production)
    import time

    time.sleep(2)  # Show splash for 2 seconds

    # Close splash and show main window
    splash.finish(window)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
