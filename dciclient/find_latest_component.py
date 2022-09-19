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
from dciclient.v1.shell_commands.cli import _default_dci_cs_url
from dciclient.v1.api import context as dci_context
from dciclient.v1.shell_commands import component
from dciclient.v1.shell_commands import topic
from dciclient.v1.shell_commands import product
from dciclient.printer import print_result


COLUMNS = ["canonical_project_name",
           "created_at",
           "data",
           "etag",
           "id",
           "message",
           "name",
           "released_at",
           "state",
           "tags",
           "team_id",
           "title",
           "topic_id",
           "type",
           "updated_at",
           "url",
           ]


def parse_arguments(args, environment={}):
    p = ArgumentParser(
        prog="dci-find-latest-component",
        description=(
            "Tool to find latest component using a Remote CI "
            "(https://docs.distributed-ci.io/#remote-ci)"
        ),
    )
    p.add_argument("--verbose", "--long", default=False, action="store_true")
    p.add_argument("--version", action="version", version="%(prog)s " + __version__)
    p.add_argument(
        "--dci-client-id",
        default=environment.get("DCI_CLIENT_ID", None),
        help="DCI CLIENT ID or 'DCI_CLIENT_ID' environment variable.",
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
    _create_array_argument(p, "--tags", help="Comma separated list of tags")
    p.add_argument(
        "--format",
        default=os.environ.get("DCI_FORMAT", "table"),
        choices=["table", "json", "csv", "tsv"],
        help="Output format",
    )
    p.add_argument(
        "--topic",
        help="Topic type and version, examples: OCP-4.12 or RHEL-9.1",
    )
    p.add_argument(
        "product",
        help=("Product to look for the component. "
              "For example, OpenShift, OpenStack or RHEL."),
    )
    p.add_argument(
        "type",
        help='Name of the component, example: my-awesome-component',
        metavar="component_name",
    )
    args = p.parse_args(args)
    args.command = "component-list"

    return args


def get_product_id(context, args):
    a = copy.deepcopy(args)

    # Set defaults
    a.sort = "-created_at"
    a.limit = 1
    a.offset = 0
    a.where = "name:" + a.product

    response = product.list(context, a)
    try:
        result_json = response.json()
    except Exception:
        print(response)

    if not result_json["_meta"]["count"]:
        sys.stderr.write("Error, product %s was not found\n" % a.product)
        return None

    return result_json["products"][0].get("id")


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
        sys.stderr.write(response)
        return None

    if not result_json["_meta"]["count"]:
        sys.stderr.write("Error, topic '%s' was not found\n" % args.topic)
        return None

    return result_json["topics"][0].get("id")


def get_topic_ids(context, args):
    a = copy.deepcopy(args)

    # Set defaults
    a.where = None
    a.sort = "-created_at"
    a.limit = 50
    a.offset = 0

    response = topic.list(context, a)
    try:
        result_json = response.json()
    except Exception:
        sys.stderr.write(response)
        return []

    if not result_json["_meta"]["count"]:
        sys.stderr.write("Error, no topic '%s' was found\n" % args.topic)
        return []

    return [res.get("id") for res in result_json["topics"]]


def lookup_component(context, args):
    a = copy.deepcopy(args)

    # Set defaults
    a.where = "type:" + a.type + ((",tags:" + ",".join(a.tags))
                                  if len(a.tags) != 0 else "")
    a.sort = "-released_at"
    a.limit = 1
    a.offset = 0
    a.id = a.topic_id

    response = component.list(context, a)
    try:
        result_json = response.json()
    except Exception:
        sys.stderr.write(response)
        return None
    if not result_json["_meta"]["count"]:
        return None

    return result_json["components"][0]


def run(context, args):
    args.product_id = get_product_id(context, args)

    if args.topic:
        args.topic_id = get_topic_id(context, args)
        return lookup_component(context, args)
    else:
        for topic_id in get_topic_ids(context, args):
            args.topic_id = topic_id
            comp = lookup_component(context, args)
            if comp:
                return comp
    return None


def main():
    args = parse_arguments(sys.argv[1:], os.environ)

    dci_cs_url = args.dci_cs_url
    dci_client_id = args.dci_client_id
    dci_api_secret = args.dci_api_secret
    context = None

    if dci_client_id is not None and dci_api_secret is not None:
        context = dci_context.build_signature_context(
            dci_cs_url=dci_cs_url,
            dci_client_id=dci_client_id,
            dci_api_secret=dci_api_secret,
        )
    if not context:
        sys.stderr.write("No Remote CI credentials provided\n.")
        return 1

    result = run(context, args)
    if result:
        print_result(result, args.format, args.verbose, COLUMNS)
        return 0
    else:
        sys.stderr.write("No component found for %s on the %s product\n"
                         % (args.type, args.product))
        return 1
