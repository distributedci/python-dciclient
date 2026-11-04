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
import time
import base64
import tempfile
import os
import pytest
import responses

from dciclient.v1.api.context import JWTBearerAuth, JWTContext, build_jwt_context
from dciclient.v1.api.token_storage import TokenStorage


def create_jwt_token(payload):
    """Helper to create a minimal JWT token for testing"""
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    signature = "fake_signature"
    return f"{header_b64}.{payload_b64}.{signature}"


@responses.activate
def test_jwt_bearer_auth_with_valid_token():
    storage = TokenStorage(token_file=False)
    current_time = int(time.time())

    access_token = create_jwt_token({"exp": current_time + 3600})
    refresh_token = create_jwt_token({"exp": current_time + 86400})

    storage.save_tokens(access_token, refresh_token)

    auth = JWTBearerAuth("http://localhost:5000", storage)

    class MockRequest:
        def __init__(self):
            self.headers = {}

    request = MockRequest()
    result = auth(request)

    assert result.headers["Authorization"] == f"JWTBearer {access_token}"


@responses.activate
def test_jwt_bearer_auth_refreshes_expired_token():
    storage = TokenStorage(token_file=False)
    current_time = int(time.time())

    access_token_expired = create_jwt_token({"exp": current_time - 100})
    refresh_token = create_jwt_token({"exp": current_time + 86400})

    storage.save_tokens(access_token_expired, refresh_token)

    new_access_token = create_jwt_token({"exp": current_time + 3600})
    new_refresh_token = create_jwt_token({"exp": current_time + 86400})

    responses.add(
        method=responses.POST,
        url="http://localhost:5000/api/v1/auth/refresh",
        json={
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
        },
        status=200,
    )

    auth = JWTBearerAuth("http://localhost:5000", storage)

    class MockRequest:
        def __init__(self):
            self.headers = {}

    request = MockRequest()
    result = auth(request)

    assert result.headers["Authorization"] == f"JWTBearer {new_access_token}"

    tokens = storage.load_tokens()
    assert tokens["access_token"] == new_access_token
    assert tokens["refresh_token"] == new_refresh_token


@responses.activate
def test_jwt_bearer_auth_refresh_failure():
    storage = TokenStorage(token_file=False)
    current_time = int(time.time())

    access_token_expired = create_jwt_token({"exp": current_time - 100})
    refresh_token = create_jwt_token({"exp": current_time + 86400})

    storage.save_tokens(access_token_expired, refresh_token)

    responses.add(
        method=responses.POST,
        url="http://localhost:5000/api/v1/auth/refresh",
        json={"message": "Invalid refresh token"},
        status=401,
    )

    auth = JWTBearerAuth("http://localhost:5000", storage)

    class MockRequest:
        def __init__(self):
            self.headers = {}

    request = MockRequest()

    with pytest.raises(Exception) as exc_info:
        auth(request)

    assert "Failed to refresh token" in str(exc_info.value)


def test_jwt_bearer_auth_no_refresh_token():
    storage = TokenStorage(token_file=False)
    current_time = int(time.time())

    access_token_expired = create_jwt_token({"exp": current_time - 100})
    refresh_token_expired = create_jwt_token({"exp": current_time - 100})

    storage.save_tokens(access_token_expired, refresh_token_expired)

    auth = JWTBearerAuth("http://localhost:5000", storage)

    class MockRequest:
        def __init__(self):
            self.headers = {}

    request = MockRequest()

    with pytest.raises(Exception) as exc_info:
        auth(request)

    assert "No valid refresh token available" in str(exc_info.value)


def test_jwt_context_initialization():
    storage = TokenStorage(token_file=False)
    current_time = int(time.time())

    access_token = create_jwt_token({"exp": current_time + 3600})
    refresh_token = create_jwt_token({"exp": current_time + 86400})

    storage.save_tokens(access_token, refresh_token)

    context = JWTContext("http://localhost:5000", token_storage=storage)

    assert context.dci_cs_api == "http://localhost:5000/api/v1"
    assert context.session.auth is not None
    assert isinstance(context.session.auth, JWTBearerAuth)


def test_build_jwt_context_missing_url(monkeypatch):
    monkeypatch.delenv("DCI_CS_URL", raising=False)

    with pytest.raises(Exception) as exc_info:
        build_jwt_context(dci_cs_url=None)

    assert "DCI_CS_URL is required" in str(exc_info.value)


def test_build_jwt_context_no_tokens():
    with tempfile.TemporaryDirectory() as tmpdir:
        token_file = os.path.join(tmpdir, "tokens.json")
        storage = TokenStorage(token_file=token_file)

        with pytest.raises(Exception) as exc_info:
            build_jwt_context(
                dci_cs_url="http://localhost:5000",
                token_storage=storage,
            )

        assert "No JWT tokens found" in str(exc_info.value)


def test_build_jwt_context_with_tokens():
    with tempfile.TemporaryDirectory() as tmpdir:
        token_file = os.path.join(tmpdir, "tokens.json")
        storage = TokenStorage(token_file=token_file)

        current_time = int(time.time())
        access_token = create_jwt_token({"exp": current_time + 3600})
        refresh_token = create_jwt_token({"exp": current_time + 86400})

        storage.save_tokens(access_token, refresh_token)

        context = build_jwt_context(
            dci_cs_url="http://localhost:5000",
            token_storage=storage,
        )

        assert context is not None
        assert isinstance(context, JWTContext)


@responses.activate
def test_jwt_context_login():
    storage = TokenStorage(token_file=False)
    context = JWTContext("http://localhost:5000", token_storage=storage)

    current_time = int(time.time())
    new_access_token = create_jwt_token({"exp": current_time + 3600})
    new_refresh_token = create_jwt_token({"exp": current_time + 86400})

    responses.add(
        method=responses.POST,
        url="http://localhost:5000/api/v1/auth/login",
        json={
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
        },
        status=200,
    )

    context.login("user@example.org", "password")

    tokens = storage.load_tokens()
    assert tokens["access_token"] == new_access_token
    assert tokens["refresh_token"] == new_refresh_token


@responses.activate
def test_jwt_context_login_failure():
    storage = TokenStorage(token_file=False)
    context = JWTContext("http://localhost:5000", token_storage=storage)

    responses.add(
        method=responses.POST,
        url="http://localhost:5000/api/v1/auth/login",
        json={"message": "Invalid credentials"},
        status=401,
    )

    with pytest.raises(Exception):
        context.login("user@example.org", "wrongpassword")
