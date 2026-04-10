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

import pytest
import responses
import logging
import json
import time
import base64

from dciclient.v1.api.context import DciContext


def create_jwt_token(payload):
    """Helper to create a minimal JWT token for testing"""
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    signature = "fake_signature"
    return f"{header_b64}.{payload_b64}.{signature}"


@responses.activate
def test_dci_context_deprecation_warning(caplog):
    current_time = int(time.time())
    access_token = create_jwt_token({"exp": current_time + 3600})
    refresh_token = create_jwt_token({"exp": current_time + 86400})

    responses.add(
        method=responses.POST,
        url="http://localhost:5000/api/v1/auth/login",
        json={
            "access_token": access_token,
            "refresh_token": refresh_token,
        },
        status=200,
    )

    with caplog.at_level(logging.WARNING):
        context = DciContext("http://localhost:5000", "user@example.org", "password")

    assert "DciContext is deprecated" in caplog.text
    assert "JWT authentication" in caplog.text
    assert context is not None
