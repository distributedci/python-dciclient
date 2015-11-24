# -*- encoding: utf-8 -*-
#
# Copyright 2015 Red Hat, Inc.
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

import click

from dciclient.v1.shell_commands import cli
from dciclient.v1 import utils

from dciclient.v1.handlers import test


@cli.command("test-list", help="List all tests.")
@click.pass_obj
def list(session):
    utils.print_json(test.Test(session).list().json())


@cli.command("test-create", help="Create a test.")
@click.option("--name", required=True)
@click.option("--data")
@click.pass_obj
def create(session, name, data):
    utils.print_json(
        test.Test(session)
        .create(name=name, data=data)
        .json()
    )


@cli.command("test-update", help="Update a test.")
@click.option("--id", required=True)
@click.option("--etag", required=True)
@click.option("--name")
@click.option("--data")
@click.pass_obj
def update(session, id, etag, name, data):
    result = test.Test(session).update(id=id, etag=etag, name=name, data=data)
    if result.status_code == 204:
        utils.print_json({"id": id,
                          "etag": etag,
                          "name": name,
                          "message": "Test updated."})
    else:
        utils.print_json(result.json())


@cli.command("test-delete", help="Delete a test.")
@click.option("--id", required=True)
@click.option("--etag", required=True)
@click.pass_obj
def delete(session, id, etag):
    result = test.Test(session).delete(id=id, etag=etag)
    if result.status_code == 204:
        utils.print_json({"id": id,
                          "message": "Test deleted."})
    else:
        utils.print_json(result.json())


@cli.command("test-show", help="Show a test.")
@click.option("--id", required=True)
@click.pass_obj
def show(session, id):
    result = test.Test(session).get(id=id)
    utils.print_json(result.json())
