#!/usr/bin/env python3
"""
Profile Management Dialog
"""

from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QSpinBox,
    QRadioButton,
    QButtonGroup,
    QGroupBox,
    QFileDialog,
    QCheckBox,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class ProfileDialog(QDialog):
    """Dialog for managing SSH connection profiles"""

    profile_selected = pyqtSignal(dict)  # Signal when a profile is selected

    def __init__(self, profile_manager, parent=None):
        super().__init__(parent)
        self.profile_manager = profile_manager
        self.current_profile_name = None
        self.init_ui()
        self.load_profiles()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Connection Profile Manager")
        self.setGeometry(100, 100, 600, 500)
        self.setModal(True)

        layout = QVBoxLayout(self)

        # Profile List Section
        list_group = QGroupBox("Saved Profiles")
        list_layout = QVBoxLayout(list_group)

        self.profile_list = QListWidget()
        self.profile_list.itemClicked.connect(self.on_profile_selected)
        list_layout.addWidget(self.profile_list)

        # Profile List Buttons
        list_btn_layout = QHBoxLayout()
        self.load_btn = QPushButton("Load Selected")
        self.load_btn.clicked.connect(self.load_selected_profile)
        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.clicked.connect(self.delete_selected_profile)
        self.test_btn = QPushButton("Test Connection")
        self.test_btn.clicked.connect(self.test_selected_profile)

        list_btn_layout.addWidget(self.load_btn)
        list_btn_layout.addWidget(self.delete_btn)
        list_btn_layout.addWidget(self.test_btn)
        list_layout.addLayout(list_btn_layout)

        layout.addWidget(list_group)

        # Profile Editor Section
        editor_group = QGroupBox("Profile Editor")
        editor_layout = QGridLayout(editor_group)

        # Profile Name
        editor_layout.addWidget(QLabel("Profile Name:"), 0, 0)
        self.profile_name_input = QLineEdit()
        self.profile_name_input.setPlaceholderText(
            "Enter profile name (e.g., Production Server)"
        )
        editor_layout.addWidget(self.profile_name_input, 0, 1, 1, 2)

        # Host Configuration
        editor_layout.addWidget(QLabel("Host/IP:"), 1, 0)
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("192.168.1.100 or example.com")
        editor_layout.addWidget(self.host_input, 1, 1)

        editor_layout.addWidget(QLabel("Port:"), 1, 2)
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(22)
        editor_layout.addWidget(self.port_input, 1, 3)

        editor_layout.addWidget(QLabel("Username:"), 2, 0)
        self.username_input = QLineEdit()
        editor_layout.addWidget(self.username_input, 2, 1, 1, 3)

        # Authentication
        editor_layout.addWidget(QLabel("Authentication:"), 3, 0)
        self.auth_group = QButtonGroup()

        self.password_radio = QRadioButton("Password")
        self.password_radio.setChecked(True)
        self.auth_group.addButton(self.password_radio)
        editor_layout.addWidget(self.password_radio, 3, 1)

        self.key_radio = QRadioButton("Private Key")
        self.auth_group.addButton(self.key_radio)
        editor_layout.addWidget(self.key_radio, 3, 2)

        # Password input
        editor_layout.addWidget(QLabel("Password:"), 4, 0)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        editor_layout.addWidget(self.password_input, 4, 1, 1, 3)

        # Key file input
        editor_layout.addWidget(QLabel("Key File:"), 5, 0)
        self.key_file_input = QLineEdit()
        self.key_file_input.setEnabled(False)
        editor_layout.addWidget(self.key_file_input, 5, 1)

        self.browse_key_btn = QPushButton("Browse")
        self.browse_key_btn.setEnabled(False)
        self.browse_key_btn.clicked.connect(self.browse_key_file)
        editor_layout.addWidget(self.browse_key_btn, 5, 2)

        # Remote path
        editor_layout.addWidget(QLabel("Remote Path:"), 6, 0)
        self.remote_path_input = QLineEdit()
        self.remote_path_input.setPlaceholderText("/home/user/uploads/")
        editor_layout.addWidget(self.remote_path_input, 6, 1, 1, 3)

        layout.addWidget(editor_group)

        # Editor Buttons
        editor_btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save Profile")
        self.save_btn.clicked.connect(self.save_current_profile)
        self.clear_btn = QPushButton("Clear Form")
        self.clear_btn.clicked.connect(self.clear_form)

        editor_btn_layout.addWidget(self.save_btn)
        editor_btn_layout.addWidget(self.clear_btn)
        layout.addLayout(editor_btn_layout)

        # Connect authentication radio buttons
        self.password_radio.toggled.connect(self.on_auth_method_changed)
        self.key_radio.toggled.connect(self.on_auth_method_changed)

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

    def load_profiles(self):
        """Load profiles into the list"""
        self.profile_list.clear()
        profile_names = self.profile_manager.get_profile_names()
        for name in profile_names:
            item = QListWidgetItem(name)
            self.profile_list.addItem(item)

    def on_profile_selected(self, item):
        """Handle profile selection"""
        profile_name = item.text()
        profile_data = self.profile_manager.get_profile(profile_name)

        # Fill the form with profile data
        self.profile_name_input.setText(profile_name)
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

        self.current_profile_name = profile_name

    def load_selected_profile(self):
        """Load the selected profile and close dialog"""
        current_item = self.profile_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a profile to load.")
            return

        profile_name = current_item.text()
        profile_data = self.profile_manager.get_profile(profile_name)
        self.profile_selected.emit(profile_data)
        self.accept()

    def delete_selected_profile(self):
        """Delete the selected profile"""
        current_item = self.profile_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a profile to delete.")
            return

        profile_name = current_item.text()
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete the profile '{profile_name}'?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.profile_manager.delete_profile(profile_name)
            self.load_profiles()
            self.clear_form()

    def test_selected_profile(self):
        """Test connection for selected profile"""
        current_item = self.profile_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a profile to test.")
            return

        profile_name = current_item.text()
        profile_data = self.profile_manager.get_profile(profile_name)

        success, message = self.profile_manager.test_connection(profile_data)

        if success:
            QMessageBox.information(self, "Connection Test", f"✅ {message}")
        else:
            QMessageBox.critical(self, "Connection Test", f"❌ {message}")

    def save_current_profile(self):
        """Save the current profile"""
        profile_name = self.profile_name_input.text().strip()
        if not profile_name:
            QMessageBox.warning(self, "Warning", "Please enter a profile name.")
            return

        # Collect profile data
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

        # Validate required fields
        if not profile_data["host"]:
            QMessageBox.warning(self, "Warning", "Please enter a host/IP address.")
            return

        if not profile_data["username"]:
            QMessageBox.warning(self, "Warning", "Please enter a username.")
            return

        # Save profile
        self.profile_manager.save_profile(profile_name, profile_data)
        self.load_profiles()

        QMessageBox.information(
            self, "Success", f"Profile '{profile_name}' saved successfully!"
        )
        self.current_profile_name = profile_name

    def clear_form(self):
        """Clear the form"""
        self.profile_name_input.clear()
        self.host_input.clear()
        self.port_input.setValue(22)
        self.username_input.clear()
        self.password_input.clear()
        self.key_file_input.clear()
        self.remote_path_input.clear()
        self.password_radio.setChecked(True)
        self.current_profile_name = None
