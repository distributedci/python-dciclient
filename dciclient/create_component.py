# -*- encoding: utf-8 -*-
#
# Copyright 2022 Red Hat, Inc.
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

import os
import sys
import copy

from argparse import ArgumentParser
from dciclient.version import __version__
from dciclient.v1.shell_commands.cli import _create_array_argument
from dciclient.v1.shell_commands.cli import _date_isoformat
from dciclient.v1.shell_commands.cli import _default_dci_cs_url
from dciclient.v1.api import context as dci_context
from dciclient.v1.shell_commands import component
from dciclient.v1.shell_commands import topic
from dciclient.v1.shell_commands import team
from dciclient.v1.shell_commands import columns
from dciclient.printer import print_response


def parse_arguments(args, environment={}):
    p = ArgumentParser(prog="dci-create-component")
    p.add_argument("--verbose", "--long", default=False, action="store_true")
    p.add_argument("--version", action="version", version="%(prog)s " + __version__)
    p.add_argument(
        "--dci-login",
        default=environment.get("DCI_LOGIN", None),
        help="DCI login or 'DCI_LOGIN' environment variable.",
    )
    p.add_argument(
        "--dci-password",
        default=environment.get("DCI_PASSWORD", None),
        help="DCI password or 'DCI_PASSWORD' environment variable.",
    )
    p.add_argument(
        "--dci-client-id",
        default=environment.get("DCI_CLIENT_ID", None),
        help="DCI CLIENt ID or 'DCI_CLIENT_ID' environment variable.",
    )
    p.add_argument(
        "--dci-api-secret",
        default=environment.get("DCI_API_SECRET", None),
        help="DCI API secret or 'DCI_API_SECRET' environment variable.",
    )
    p.add_argument(
        "--dci-cs-url",
        default=environment.get("DCI_CS_URL", _default_dci_cs_url),
        help="DCI control server url, default to '%s'." % _default_dci_cs_url,
    )

    p.add_argument(
        "--team",
        help="Team name where the component will be added, default to the first team found.",
    )
    _create_array_argument(p, "--tags", help="Comma separated list of tags")
    p.add_argument(
        "--released-at",
        help="The release date",
        default=None,
        type=_date_isoformat,
    )
    p.add_argument(
        "--url",
        help="URL to look for the component",
    )
    p.add_argument(
        "--data",
        default="{}",
        help="Data to pass (JSON)",
    )
    p.add_argument(
        "topic",
        help="Topic type and version, examples: OCP-4.12 or RHEL-9.1",
    )
    p.add_argument(
        "canonical_project_name",
        help='Name of the component, example: "my awesome component"',
        metavar="component_name",
    )
    p.add_argument(
        "name",
        help="Version of the component, example: v2.3.4",
        metavar="component_version",
    )
    p.add_argument(
        "type",
        help="Release type of the component, default: dev",
        nargs="?",
        type=str,
        choices=["dev", "rc", "ga"],
        default="dev",
    )

    p.add_argument(
        "--format",
        default=os.environ.get("DCI_FORMAT", "table"),
        choices=["table", "json", "csv", "tsv"],
        help="Output format",
    )
    args = p.parse_args(args)

    return args


def get_team_id(context, args):
    a = copy.deepcopy(args)

    # Set defaults
    a.where = "name:%s" % args.team
    a.sort = "-created_at"
    a.limit = 50
    a.offset = 0

    response = team.list(context, a)
    try:
        result_json = response.json()
    except Exception:
        print(response)

    if not result_json["_meta"]["count"]:
        print("Error, no team named '%s' was found" % args.team)
        sys.exit(1)

    return result_json["teams"][0].get("id")


def get_topic_id(context, args):
    a = copy.deepcopy(args)

    # Set defaults
    a.where = "name:%s" % args.topic
    a.sort = "-created_at"
    a.limit = 50
    a.offset = 0

    response = topic.list(context, a)
    try:
        result_json = response.json()
    except Exception:
        print(response)

    if not result_json["_meta"]["count"]:
        print("Error, no topic '%s' was found" % args.topic)
        sys.exit(1)

    return result_json["topics"][0].get("id")


def run(context, args):
    args.team_id = get_team_id(context, args)
    args.topic_id = get_topic_id(context, args)

    # Required arguments for component creation
    args.title = None
    args.message = None
    args.state = True
    args.command = "component-create"

    return component.create(context, args)


def main():
    args = parse_arguments(sys.argv[1:], os.environ)

    dci_cs_url = args.dci_cs_url
    dci_login = args.dci_login
    dci_password = args.dci_password
    context = None
    if dci_login is not None and dci_password is not None:
        context = dci_context.build_dci_context(
            dci_login=dci_login, dci_password=dci_password, dci_cs_url=dci_cs_url
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
        print("No credentials provided.")
        sys.exit(1)

    response = run(context, args)
    _columns = columns.get_columns(args)
    print_response(response, args.format, args.verbose, _columns)
