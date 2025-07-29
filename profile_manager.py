#!/usr/bin/env python3
"""
Profile Manager for SSH Connection Profiles
"""

import json
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import getpass
import platform


class ProfileManager:
    """Manages SSH connection profiles with encrypted storage"""

    def __init__(self, profiles_file="profiles.json"):
        self.profiles_file = profiles_file
        self.profiles = {}
        self.encryption_key = None
        self._load_profiles()

    def _get_encryption_key(self):
        """Generate or retrieve encryption key based on system"""
        if self.encryption_key:
            return self.encryption_key

        # Use system-specific salt for key derivation
        system_info = f"{platform.system()}-{platform.machine()}-{getpass.getuser()}"
        salt = system_info.encode()

        # Generate key from system info
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(system_info.encode()))
        self.encryption_key = key
        return key

    def _encrypt_password(self, password):
        """Encrypt password for storage"""
        if not password:
            return ""

        fernet = Fernet(self._get_encryption_key())
        encrypted = fernet.encrypt(password.encode())
        return base64.urlsafe_b64encode(encrypted).decode()

    def _decrypt_password(self, encrypted_password):
        """Decrypt password from storage"""
        if not encrypted_password:
            return ""

        try:
            fernet = Fernet(self._get_encryption_key())
            encrypted = base64.urlsafe_b64decode(encrypted_password.encode())
            decrypted = fernet.decrypt(encrypted)
            return decrypted.decode()
        except Exception:
            return ""

    def _load_profiles(self):
        """Load profiles from JSON file"""
        try:
            if os.path.exists(self.profiles_file):
                with open(self.profiles_file, "r") as f:
                    data = json.load(f)
                    # Decrypt passwords
                    for profile_name, profile_data in data.items():
                        if "password" in profile_data:
                            profile_data["password"] = self._decrypt_password(
                                profile_data["password"]
                            )
                    self.profiles = data
        except Exception as e:
            print(f"Warning: Could not load profiles: {e}")
            self.profiles = {}

    def _save_profiles(self):
        """Save profiles to JSON file with encrypted passwords"""
        try:
            # Create a copy for saving with encrypted passwords
            save_data = {}
            for profile_name, profile_data in self.profiles.items():
                save_data[profile_name] = profile_data.copy()
                if "password" in save_data[profile_name]:
                    save_data[profile_name]["password"] = self._encrypt_password(
                        save_data[profile_name]["password"]
                    )

            with open(self.profiles_file, "w") as f:
                json.dump(save_data, f, indent=2)
        except Exception as e:
            print(f"Error saving profiles: {e}")

    def get_profile_names(self):
        """Get list of profile names"""
        return list(self.profiles.keys())

    def get_profile(self, profile_name):
        """Get profile data by name"""
        return self.profiles.get(profile_name, {})

    def save_profile(self, profile_name, profile_data):
        """Save a new profile or update existing one"""
        self.profiles[profile_name] = profile_data.copy()
        self._save_profiles()

    def delete_profile(self, profile_name):
        """Delete a profile"""
        if profile_name in self.profiles:
            del self.profiles[profile_name]
            self._save_profiles()
            return True
        return False

    def test_connection(self, profile_data):
        """Test SSH connection with profile data"""
        try:
            import paramiko

            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            if profile_data.get("auth_method") == "password":
                ssh.connect(
                    profile_data["host"],
                    port=profile_data.get("port", 22),
                    username=profile_data["username"],
                    password=profile_data.get("password", ""),
                    timeout=10,
                )
            else:
                ssh.connect(
                    profile_data["host"],
                    port=profile_data.get("port", 22),
                    username=profile_data["username"],
                    key_filename=profile_data.get("key_file", ""),
                    timeout=10,
                )

            ssh.close()
            return True, "Connection successful"

        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    def export_profiles(self, export_file):
        """Export profiles to file"""
        try:
            with open(export_file, "w") as f:
                json.dump(self.profiles, f, indent=2)
            return True
        except Exception:
            return False

    def import_profiles(self, import_file):
        """Import profiles from file"""
        try:
            with open(import_file, "r") as f:
                imported_profiles = json.load(f)

            # Merge with existing profiles
            self.profiles.update(imported_profiles)
            self._save_profiles()
            return True
        except Exception:
            return False
