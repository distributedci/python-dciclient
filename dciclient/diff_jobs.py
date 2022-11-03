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

from argparse import ArgumentParser
from dciclient.v1.api import job as dci_job
from dciclient.v1.shell_commands import context as dci_context
from dciclient.printer import print_result


def get_component_info(comp):
    if comp["type"] in ("rpm", "git"):
        c_type, c_name = comp["name"].split(" ", 1)
        return (c_type, c_name)
    else:
        return (comp["type"], comp["name"])


def run(context, args):
    if args.job_id_1 is None:
        sys.stderr.write("no job_id_1 provided, getting latest job\n")
        jobs = dci_job.list(context, limit=1, offset=0).json()["jobs"]
        job_1 = jobs[0]
        args.job_id_1 = job_1["id"]
    else:
        job_1 = dci_job.get(context, args.job_id_1).json()["job"]
    job_name = job_1["name"]

    if args.job_id_2 is None:
        sys.stderr.write("no job_id_2 provided, getting job with the name %s\n"
                         % job_name)
        if job_name is None:
            job = dci_job.get(context, args.job_id_1).json()["job"]
            job_name = job["name"]
        jobs = dci_job.list(context,
                            limit=2,
                            offset=0,
                            where="name:%s" % job_name,
                            sort="-created_at").json()["jobs"]
        job_2 = jobs[1]
        args.job_id_2 = job_2["id"]
    else:
        job_2 = dci_job.get(context, args.job_id_2).json()["job"]

    data1 = {}
    data2 = {}
    if args.tags:
        for c in job_1["tags"]:
            data1[c] = c
        for c in job_2["tags"]:
            data2[c] = c
        key = "tag"
    else:
        for c in job_1["components"]:
            c_type, c_name = get_component_info(c)
            data1[c_type] = c_name
        for c in job_2["components"]:
            c_type, c_name = get_component_info(c)
            data2[c_type] = c_name
        key = "component"
    table = []
    for c1 in data1:
        if c1 in data2:
            if data1[c1] != data2[c1]:
                table.append({key: c1,
                              args.job_id_1: data1[c1],
                              args.job_id_2: data2[c1],
                              })
        else:
            table.append({key: c1,
                          args.job_id_1: data1[c1],
                          args.job_id_2: "Not found",
                          })
    for c2 in data2:
        if c2 not in data1:
            table.append({key: c2,
                          args.job_id_1: "Not found",
                          args.job_id_2: data2[c2],
                          })
    return table


def parse_arguments(args, environment={}):
    p = ArgumentParser(
        prog="dci-diff-jobs",
        description=(
            "Tool to compare 2 DCI jobs (components or tags)"
            "(https://docs.distributed-ci.io/)"
        ),
    )
    dci_context.parse_arguments(p, args, environment)
    p.add_argument(
        "--tags",
        default=False,
        action="store_true",
        help="Display tags instead of components",
    )
    p.add_argument(
        "--job_id_1",
        help="First job id",
        type=str,
        default=None,
    )
    p.add_argument(
        "--job_id_2",
        help="Second job id",
        type=str,
        default=None,
    )
    args = p.parse_args(args)
    args.command = "diff-jobs"

    return args


def main():
    args = parse_arguments(sys.argv[1:], os.environ)

    context = dci_context.build_context(args)

    if not context:
        print("No DCI credentials provided.")
        sys.exit(1)

    response = run(context, args)
    print_result(response, args.format, args.verbose,
                 [args.job_id_1, args.job_id_2] if args.tags else
                 ["component", args.job_id_1, args.job_id_2])
