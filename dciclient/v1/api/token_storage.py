# Copyright 2026 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import json
import os
import time
import base64


class TokenStorage:
    """Manages JWT token storage on disk or in-memory"""

    def __init__(self, token_file=None):
        if token_file is False:
            self.token_file = None
            self._tokens = None
        elif token_file is None:
            xdg_state_home = os.environ.get(
                "XDG_STATE_HOME",
                os.path.join(os.path.expanduser("~"), ".local", "state")
            )
            dci_dir = os.path.join(xdg_state_home, "dci")
            self.token_file = os.path.join(dci_dir, "tokens.json")
            self._tokens = None
        else:
            self.token_file = token_file
            self._tokens = None

    @staticmethod
    def _decode_jwt_payload(token):
        """
        Decode JWT payload without verification to extract claims.

        Args:
            token: JWT token string

        Returns:
            dict: Decoded payload
            None: If token cannot be decoded
        """
        try:
            # JWT format: header.payload.signature
            parts = token.split(".")
            if len(parts) != 3:
                return None

            # Decode payload (add padding if needed)
            payload = parts[1]
            padding = 4 - (len(payload) % 4)
            if padding != 4:
                payload += "=" * padding

            decoded = base64.urlsafe_b64decode(payload)
            return json.loads(decoded)
        except (ValueError, json.JSONDecodeError, Exception):
            return None

    def save_tokens(self, access_token, refresh_token):
        """
        Save JWT tokens to disk or memory, extracting expiry from tokens themselves.

        Args:
            access_token: JWT access token
            refresh_token: JWT refresh token
        """
        # Extract expiration times from both tokens
        access_payload = self._decode_jwt_payload(access_token)
        refresh_payload = self._decode_jwt_payload(refresh_token)

        access_expires_at = access_payload.get("exp") if access_payload else None
        refresh_expires_at = refresh_payload.get("exp") if refresh_payload else None

        # If we can't decode, set defaults
        current_time = int(time.time())
        if not access_expires_at:
            access_expires_at = current_time + 3600  # 1 hour default
        if not refresh_expires_at:
            refresh_expires_at = current_time + 86400  # 24 hours default

        tokens = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "access_expires_at": access_expires_at,
            "refresh_expires_at": refresh_expires_at,
        }

        # In-memory storage
        if self.token_file is None:
            self._tokens = tokens
            return

        # File-based storage
        token_dir = os.path.dirname(self.token_file)
        if not os.path.exists(token_dir):
            os.makedirs(token_dir, mode=0o700)

        with open(self.token_file, "w") as f:
            json.dump(tokens, f, indent=2)

        # Ensure file permissions are secure (user read/write only)
        os.chmod(self.token_file, 0o600)

    def load_tokens(self):
        """
        Load JWT tokens from disk or memory.

        Returns:
            dict: Token data with keys: access_token, refresh_token,
                  access_expires_at, refresh_expires_at
            None: If no tokens exist
        """
        # In-memory storage
        if self.token_file is None:
            return self._tokens

        # File-based storage
        if not os.path.exists(self.token_file):
            return None

        try:
            with open(self.token_file, "r") as f:
                tokens = json.load(f)

            # Validate token structure
            required_keys = ["access_token", "refresh_token", "access_expires_at", "refresh_expires_at"]
            if not all(k in tokens for k in required_keys):
                return None

            return tokens
        except (json.JSONDecodeError, IOError):
            return None

    def remove_tokens(self):
        """Remove stored tokens from disk"""
        if os.path.exists(self.token_file):
            os.remove(self.token_file)

    def is_access_token_expired(self, buffer_seconds=300):
        """
        Check if the stored access token is expired or will expire soon.

        Args:
            buffer_seconds: Seconds before expiry to consider token as expired
                          (default 300 = 5 minutes)

        Returns:
            bool: True if token is expired or will expire soon, False otherwise
        """
        tokens = self.load_tokens()
        if not tokens:
            return True

        expires_at = tokens.get("access_expires_at", 0)
        current_time = int(time.time())

        # Token is expired if current time + buffer is past expiry
        return (current_time + buffer_seconds) >= expires_at

    def is_refresh_token_expired(self):
        """
        Check if the stored refresh token is expired.

        Returns:
            bool: True if token is expired, False otherwise
        """
        tokens = self.load_tokens()
        if not tokens:
            return True

        expires_at = tokens.get("refresh_expires_at", 0)
        current_time = int(time.time())

        return current_time >= expires_at

    def get_valid_access_token(self):
        """
        Get a valid access token if available and not expired.

        Returns:
            str: Access token if valid
            None: If no token or token is expired
        """
        if self.is_access_token_expired():
            return None

        tokens = self.load_tokens()
        return tokens.get("access_token") if tokens else None

    def get_refresh_token(self):
        """
        Get the refresh token if not expired.

        Returns:
            str: Refresh token
            None: If no token exists or is expired
        """
        if self.is_refresh_token_expired():
            return None

        tokens = self.load_tokens()
        return tokens.get("refresh_token") if tokens else None
