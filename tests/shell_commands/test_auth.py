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

import tempfile
import os
import responses

from dciclient.v1.shell_commands import auth
from dciclient.v1.api.token_storage import TokenStorage


class MockArgs:
    def __init__(self, dci_cs_url, dci_login, dci_password):
        self.dci_cs_url = dci_cs_url
        self.dci_login = dci_login
        self.dci_password = dci_password


@responses.activate
def test_login_success():
    with tempfile.TemporaryDirectory() as tmpdir:
        token_file = os.path.join(tmpdir, "tokens.json")
        original_init = TokenStorage.__init__

        def mock_init(self, token_file_arg=None):
            original_init(self, token_file=token_file)

        TokenStorage.__init__ = mock_init

        try:
            args = MockArgs(
                dci_cs_url="http://localhost:5000",
                dci_login="user@example.org",
                dci_password="password",
            )

            responses.add(
                method=responses.POST,
                url="http://localhost:5000/api/v1/auth/login",
                json={
                    "access_token": "fake_access_token",
                    "refresh_token": "fake_refresh_token",
                },
                status=200,
            )

            result = auth.login(None, args)

            assert result["login"]["status"] == "success"
            assert "Successfully logged in" in result["login"]["message"]
            assert os.path.exists(token_file)

            storage = TokenStorage()
            tokens = storage.load_tokens()
            assert tokens["access_token"] == "fake_access_token"
            assert tokens["refresh_token"] == "fake_refresh_token"

        finally:
            TokenStorage.__init__ = original_init


@responses.activate
def test_login_invalid_credentials():
    args = MockArgs(
        dci_cs_url="http://localhost:5000",
        dci_login="user@example.org",
        dci_password="wrongpassword",
    )

    responses.add(
        method=responses.POST,
        url="http://localhost:5000/api/v1/auth/login",
        json={"message": "Invalid email or password"},
        status=401,
    )

    result = auth.login(None, args)

    assert result["login"]["status"] == "error"
    assert result["login"]["message"] == "Invalid email or password"
    assert result["login"]["status_code"] == 401


@responses.activate
def test_login_server_error():
    args = MockArgs(
        dci_cs_url="http://localhost:5000",
        dci_login="user@example.org",
        dci_password="password",
    )

    responses.add(
        method=responses.POST,
        url="http://localhost:5000/api/v1/auth/login",
        json={"message": "Internal server error"},
        status=500,
    )

    result = auth.login(None, args)

    assert result["login"]["status"] == "error"
    assert "Login failed" in result["login"]["message"]


def test_login_missing_credentials():
    args = MockArgs(
        dci_cs_url="http://localhost:5000",
        dci_login=None,
        dci_password="password",
    )

    result = auth.login(None, args)

    assert result["login"]["status"] == "error"
    assert "Email and password are required" in result["login"]["message"]


@responses.activate
def test_login_missing_tokens_in_response():
    args = MockArgs(
        dci_cs_url="http://localhost:5000",
        dci_login="user@example.org",
        dci_password="password",
    )

    responses.add(
        method=responses.POST,
        url="http://localhost:5000/api/v1/auth/login",
        json={"access_token": "fake_access_token"},
        status=200,
    )

    result = auth.login(None, args)

    assert result["login"]["status"] == "error"
    assert "missing tokens" in result["login"]["message"]


def test_logout_with_tokens():
    with tempfile.TemporaryDirectory() as tmpdir:
        token_file = os.path.join(tmpdir, "tokens.json")
        original_init = TokenStorage.__init__

        def mock_init(self, token_file_arg=None):
            original_init(self, token_file=token_file)

        TokenStorage.__init__ = mock_init

        try:
            storage = TokenStorage()
            storage.save_tokens("fake_access_token", "fake_refresh_token")

            assert os.path.exists(token_file)

            result = auth.logout(None, None)

            assert result["logout"]["status"] == "success"
            assert "Successfully logged out" in result["logout"]["message"]
            assert not os.path.exists(token_file)

        finally:
            TokenStorage.__init__ = original_init


def test_logout_without_tokens():
    with tempfile.TemporaryDirectory() as tmpdir:
        token_file = os.path.join(tmpdir, "tokens.json")
        original_init = TokenStorage.__init__

        def mock_init(self, token_file_arg=None):
            original_init(self, token_file=token_file)

        TokenStorage.__init__ = mock_init

        try:
            result = auth.logout(None, None)

            assert result["logout"]["status"] == "info"
            assert "No tokens found" in result["logout"]["message"]

        finally:
            TokenStorage.__init__ = original_init
