# -*- encoding: utf-8 -*-
#
# Copyright 2026 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import json
import os
import tempfile
import time
import base64
import pytest

from dciclient.v1.api.token_storage import TokenStorage


def create_jwt_token(payload):
    """Helper to create a minimal JWT token for testing"""
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    signature = "fake_signature"
    return f"{header_b64}.{payload_b64}.{signature}"


def test_token_storage_in_memory():
    storage = TokenStorage(token_file=False)
    assert storage.token_file is None

    current_time = int(time.time())
    access_token = create_jwt_token({"exp": current_time + 3600})
    refresh_token = create_jwt_token({"exp": current_time + 86400})

    storage.save_tokens(access_token, refresh_token)

    tokens = storage.load_tokens()
    assert tokens is not None
    assert tokens["access_token"] == access_token
    assert tokens["refresh_token"] == refresh_token
    assert tokens["access_expires_at"] == current_time + 3600
    assert tokens["refresh_expires_at"] == current_time + 86400


def test_token_storage_file_based():
    with tempfile.TemporaryDirectory() as tmpdir:
        token_file = os.path.join(tmpdir, "tokens.json")
        storage = TokenStorage(token_file=token_file)

        current_time = int(time.time())
        access_token = create_jwt_token({"exp": current_time + 3600})
        refresh_token = create_jwt_token({"exp": current_time + 86400})

        storage.save_tokens(access_token, refresh_token)

        assert os.path.exists(token_file)

        stat_info = os.stat(token_file)
        assert stat_info.st_mode & 0o777 == 0o600

        tokens = storage.load_tokens()
        assert tokens is not None
        assert tokens["access_token"] == access_token
        assert tokens["refresh_token"] == refresh_token


def test_token_storage_xdg_state_home(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        xdg_state_home = os.path.join(tmpdir, "state")
        monkeypatch.setenv("XDG_STATE_HOME", xdg_state_home)

        storage = TokenStorage()

        expected_path = os.path.join(xdg_state_home, "dci", "tokens.json")
        assert storage.token_file == expected_path

        current_time = int(time.time())
        access_token = create_jwt_token({"exp": current_time + 3600})
        refresh_token = create_jwt_token({"exp": current_time + 86400})

        storage.save_tokens(access_token, refresh_token)

        assert os.path.exists(expected_path)

        tokens = storage.load_tokens()
        assert tokens is not None


def test_token_storage_default_path():
    storage = TokenStorage()
    expected_path = os.path.join(
        os.path.expanduser("~"), ".local", "state", "dci", "tokens.json"
    )
    assert storage.token_file == expected_path


def test_token_storage_load_nonexistent():
    with tempfile.TemporaryDirectory() as tmpdir:
        token_file = os.path.join(tmpdir, "nonexistent.json")
        storage = TokenStorage(token_file=token_file)

        tokens = storage.load_tokens()
        assert tokens is None


def test_token_storage_load_invalid_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        token_file = os.path.join(tmpdir, "tokens.json")

        with open(token_file, "w") as f:
            f.write("invalid json")

        storage = TokenStorage(token_file=token_file)
        tokens = storage.load_tokens()
        assert tokens is None


def test_token_storage_remove_tokens():
    with tempfile.TemporaryDirectory() as tmpdir:
        token_file = os.path.join(tmpdir, "tokens.json")
        storage = TokenStorage(token_file=token_file)

        current_time = int(time.time())
        access_token = create_jwt_token({"exp": current_time + 3600})
        refresh_token = create_jwt_token({"exp": current_time + 86400})

        storage.save_tokens(access_token, refresh_token)
        assert os.path.exists(token_file)

        storage.remove_tokens()
        assert not os.path.exists(token_file)


def test_is_access_token_expired():
    storage = TokenStorage(token_file=False)

    current_time = int(time.time())

    access_token = create_jwt_token({"exp": current_time + 3600})
    refresh_token = create_jwt_token({"exp": current_time + 86400})
    storage.save_tokens(access_token, refresh_token)

    assert not storage.is_access_token_expired()

    access_token_expiring_soon = create_jwt_token({"exp": current_time + 200})
    storage.save_tokens(access_token_expiring_soon, refresh_token)

    assert storage.is_access_token_expired()

    access_token_expired = create_jwt_token({"exp": current_time - 100})
    storage.save_tokens(access_token_expired, refresh_token)

    assert storage.is_access_token_expired()


def test_is_refresh_token_expired():
    storage = TokenStorage(token_file=False)

    current_time = int(time.time())

    access_token = create_jwt_token({"exp": current_time + 3600})
    refresh_token = create_jwt_token({"exp": current_time + 86400})
    storage.save_tokens(access_token, refresh_token)

    assert not storage.is_refresh_token_expired()

    refresh_token_expired = create_jwt_token({"exp": current_time - 100})
    storage.save_tokens(access_token, refresh_token_expired)

    assert storage.is_refresh_token_expired()


def test_get_valid_access_token():
    storage = TokenStorage(token_file=False)

    current_time = int(time.time())
    access_token = create_jwt_token({"exp": current_time + 3600})
    refresh_token = create_jwt_token({"exp": current_time + 86400})

    storage.save_tokens(access_token, refresh_token)

    valid_token = storage.get_valid_access_token()
    assert valid_token == access_token

    access_token_expired = create_jwt_token({"exp": current_time - 100})
    storage.save_tokens(access_token_expired, refresh_token)

    invalid_token = storage.get_valid_access_token()
    assert invalid_token is None


def test_get_refresh_token():
    storage = TokenStorage(token_file=False)

    current_time = int(time.time())
    access_token = create_jwt_token({"exp": current_time + 3600})
    refresh_token = create_jwt_token({"exp": current_time + 86400})

    storage.save_tokens(access_token, refresh_token)

    token = storage.get_refresh_token()
    assert token == refresh_token

    refresh_token_expired = create_jwt_token({"exp": current_time - 100})
    storage.save_tokens(access_token, refresh_token_expired)

    expired_token = storage.get_refresh_token()
    assert expired_token is None


def test_decode_jwt_payload_valid():
    current_time = int(time.time())
    token = create_jwt_token({"exp": current_time + 3600, "sub": "user123"})

    payload = TokenStorage._decode_jwt_payload(token)

    assert payload is not None
    assert payload["exp"] == current_time + 3600
    assert payload["sub"] == "user123"


def test_decode_jwt_payload_invalid():
    assert TokenStorage._decode_jwt_payload("invalid") is None
    assert TokenStorage._decode_jwt_payload("invalid.token") is None
    assert TokenStorage._decode_jwt_payload("") is None


def test_save_tokens_without_expiration():
    storage = TokenStorage(token_file=False)

    access_token = "header.payload.signature"
    refresh_token = "header.payload.signature"

    storage.save_tokens(access_token, refresh_token)

    tokens = storage.load_tokens()
    assert tokens is not None
    assert "access_expires_at" in tokens
    assert "refresh_expires_at" in tokens
