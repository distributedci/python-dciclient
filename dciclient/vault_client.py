#
# Copyright (C) 2022 Red Hat, Inc. 
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

'''DCI vault-id client for Ansible vault

Get the password associated with the remote CI from the control server
and pass it to ansible-vault (stdout).
'''

import argparse
import os
import sys
from argparse import ArgumentParser
from datetime import datetime

from dciclient.v1.api import context as dci_context
from dciclient.version import __version__
from dciclient.v1.api import remoteci as dci_remoteci


_default_dci_cs_url = "http://127.0.0.1:5000"
_default_sso_url = "http://127.0.0.1:8180"


def parse_arguments(args, environment={}):
    base_parser = ArgumentParser(add_help=False)
    base_parser.add_argument("--verbose", "--long", default=False, action="store_true")

    parser = ArgumentParser(prog="dci-vault-client")
    parser.add_argument(
        "--version", action="version", version="%(prog)s " + __version__
    )
    parser.add_argument(
        "--dci-login",
        default=environment.get("DCI_LOGIN", None),
        help="DCI login or 'DCI_LOGIN' environment variable.",
    )
    parser.add_argument(
        "--dci-password",
        default=environment.get("DCI_PASSWORD", None),
        help="DCI password or 'DCI_PASSWORD' environment variable.",
    )
    parser.add_argument(
        "--dci-client-id",
        default=environment.get("DCI_CLIENT_ID", None),
        help="DCI client id or 'DCI_CLIENT_ID' environment variable.",
    )
    parser.add_argument(
        "--dci-api-secret",
        default=environment.get("DCI_API_SECRET", None),
        help="DCI API secret or 'DCI_API_SECRET' environment variable.",
    )
    parser.add_argument(
        "--dci-cs-url",
        default=environment.get("DCI_CS_URL", _default_dci_cs_url),
        help="DCI control server url, default to '%s'." % _default_dci_cs_url,
    )
    parser.add_argument(
        "--sso-url",
        default=environment.get("SSO_URL", _default_sso_url),
        help="SSO url, default to '%s'." % _default_sso_url,
    )
    parser.add_argument(
        "--sso-username",
        default=environment.get("SSO_USERNAME"),
        help="SSO username or 'SSO_USERNAME' environment variable.",
    )
    parser.add_argument(
        "--sso-password",
        default=environment.get("SSO_PASSWORD"),
        help="SSO password or 'SSO_PASSWORD' environment variable.",
    )
    parser.add_argument(
        "--sso-token",
        default=environment.get("SSO_TOKEN"),
        help="SSO token or 'SSO_TOKEN' environment variable.",
    )
    parser.add_argument(
        "--refresh-sso-token",
        default=False,
        action="store_true",
        help="Refresh the token",
    )
    parser.add_argument(
        "--remoteci",
        default=environment.get("DCI_REMOTECI"),
        help="DCI remote CI id or 'DCI_REMOTECI' environment variable.",
    )
    parser.add_argument(
        "--vault-id",
        default="",
        help="Ansible Vault id.",
    )

    args = parser.parse_args(args)

    return args


def main():
    args = parse_arguments(sys.argv[1:], os.environ)
    dci_cs_url = args.dci_cs_url
    dci_login = args.dci_login
    dci_password = args.dci_password
    context = None
    remoteci_id = args.remoteci
    if dci_login is not None and dci_password is not None:
        context = dci_context.build_dci_context(
            dci_login=dci_login, dci_password=dci_password, dci_cs_url=dci_cs_url
        )
    sso_url = args.sso_url
    sso_username = args.sso_username
    sso_password = args.sso_password
    sso_token = args.sso_token
    refresh_sso_token = args.refresh_sso_token
    if (
        sso_url is not None and sso_username is not None and sso_password is not None
    ) or sso_token is not None:
        context = dci_context.build_sso_context(
            dci_cs_url,
            sso_url,
            sso_username,
            sso_password,
            sso_token,
            refresh=refresh_sso_token,
        )
    dci_client_id = args.dci_client_id
    dci_api_secret = args.dci_api_secret
    if dci_client_id is not None and dci_api_secret is not None:
        context = dci_context.build_signature_context(
            dci_cs_url=dci_cs_url,
            dci_client_id=dci_client_id,
            dci_api_secret=dci_api_secret,
        )
    if not context:
        sys.stderr.write("No credentials provided.\n")
        sys.exit(1)
    
    if not remoteci_id:
        remoteci_list = dci_remoteci.list(context)
        data = remoteci_list.json()
        if "_meta" in data and "count" in data["_meta"] and data["_meta"]['count'] > 0:
            remoteci_id = data["remotecis"][0]["id"]

    if not remoteci_id:
        sys.stderr.write("No remote ci found\n")
        sys.exit(1)

    res = dci_remoteci.password(context, remoteci_id, args.vault_id)

    if res.status_code != 200:
        sys.stderr.write(res.content)
        sys.exit(1)

    print(res.json()["password"])
