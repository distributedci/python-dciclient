# -*- encoding: utf-8 -*-
#
# Copyright 2015-2016 Red Hat, Inc.
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

from dciclient.v1.api import job


@cli.command("job-list", help="List all jobs.")
@click.pass_obj
def list(context):
    """List all jobs.

    >>> dcictl job-list
    """
    result = job.list(context)
    utils.format_output(result, context.format,
                        job.RESOURCE, job.TABLE_HEADERS)


@cli.command("job-show", help="Show a job.")
@click.option("--id", required=True)
@click.pass_obj
def show(context, id):
    """show(context, id)

    Show a job.

    >>> dcictl job-show [OPTIONS]

    :param string id: ID of the job to show [required]
    """
    result = job.get(context, id=id)
    utils.format_output(result, context.format,
                        job.RESOURCE[:-1], job.TABLE_HEADERS)


@cli.command("job-delete", help="Delete a job.")
@click.option("--id", required=True)
@click.option("--etag", required=True)
@click.pass_obj
def delete(context, id, etag):
    """delete(context, id, etag)

    Delete a job.

    >>> dcictl job-delete [OPTIONS]

    :param string id: ID of the job to delete [required]
    :param string etag: Entity tag of the job resource [required]
    """
    result = job.delete(context, id=id, etag=etag)
    if result.status_code == 204:
        utils.print_json({'id': id, 'message': 'Job deleted.'})
    else:
        utils.format_output(result, context.format)


@cli.command("job-recheck", help="Recheck a job.")
@click.option("--id", required=True)
@click.pass_obj
def recheck(context, id):
    """recheck(context, id)

    Reecheck a job.

    >>> dcictl job-recheck [OPTIONS]

    :param string id: ID of the job to recheck [required]
    """
    result = job.recheck(context, id=id)
    utils.format_output(result, context.format, job.RESOURCE[:-1])


@cli.command("job-results", help="List all job results.")
@click.option("--id", required=True)
@click.pass_obj
def list_results(context, id):
    """list_result(context, id)

    List all job results.

    >>> dcictl job-results

    :param string id: ID of the job to recheck [required]
    """

    headers = ['filename', 'name', 'total', 'success', 'failures', 'errors',
               'skips', 'time']
    result = job.list_results(context, id=id)
    utils.format_output(result, context.format,
                        'results', headers)
