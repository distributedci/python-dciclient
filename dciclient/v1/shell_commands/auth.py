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

import requests
from dciclient.v1.api.token_storage import TokenStorage
from dciclient.v1.api.context import DciContext


def login(context, args):
    """Login and store JWT tokens"""
    # Get credentials from args or environment
    dci_cs_url = args.dci_cs_url
    email = args.dci_login
    password = args.dci_password

    if not email or not password:
        return {
            "login": {
                "status": "error",
                "message": "Email and password are required. Use --dci-login and --dci-password or set DCI_LOGIN and DCI_PASSWORD environment variables.",
            }
        }

    # Call /auth/login endpoint
    login_url = "%s/%s/auth/login" % (dci_cs_url, DciContext.API_VERSION)

    try:
        response = requests.post(
            login_url,
            json={"email": email, "password": password},
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()

        tokens = response.json()
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")

        if not access_token or not refresh_token:
            return {
                "login": {
                    "status": "error",
                    "message": "Invalid response from server: missing tokens",
                }
            }

        # Save tokens
        token_storage = TokenStorage()
        token_storage.save_tokens(access_token, refresh_token)

        token_path = token_storage.token_file
        return {
            "login": {
                "status": "success",
                "message": "Successfully logged in. Tokens saved to %s" % token_path,
            }
        }

    except requests.exceptions.HTTPError as e:
        error_msg = "Login failed"
        if e.response.status_code == 401:
            error_msg = "Invalid email or password"
        elif e.response.status_code == 400:
            try:
                error_data = e.response.json()
                error_msg = error_data.get("message", error_msg)
            except:
                pass

        return {
            "login": {
                "status": "error",
                "message": error_msg,
                "status_code": e.response.status_code,
            }
        }
    except requests.exceptions.RequestException as e:
        return {
            "login": {
                "status": "error",
                "message": "Failed to connect to DCI server: %s" % str(e),
            }
        }


def logout(context, args):
    """Remove stored JWT tokens"""
    token_storage = TokenStorage()

    if not token_storage.load_tokens():
        return {
            "logout": {
                "status": "info",
                "message": "No tokens found. Already logged out.",
            }
        }

    token_storage.remove_tokens()

    return {
        "logout": {
            "status": "success",
            "message": "Successfully logged out. Tokens removed.",
        }
    }
