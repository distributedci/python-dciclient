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

from dci.server.tests import conftest as server_conftest
from dciclient.v1.handlers import component
from dciclient.v1.handlers import job
from dciclient.v1.handlers import jobdefinition
from dciclient.v1.handlers import remoteci
from dciclient.v1.handlers import team
from dciclient.v1.handlers import test


from dciclient import v1 as dci_client

import click.testing
import dciclient.shell as shell
import dciclient.v1.shell_commands as commands
import dciclient.v1.tests.utils as utils
import functools
import pytest


@pytest.fixture(scope='session')
def engine(request):
    return server_conftest.engine(request)


@pytest.fixture
def db_clean(request, engine):
    return server_conftest.db_clean(request, engine)


@pytest.fixture
def db_provisioning(db_clean, engine):
    server_conftest.db_provisioning(db_clean, engine)


@pytest.fixture
def server(db_provisioning, engine):
    return server_conftest.app(db_provisioning, engine)


@pytest.fixture
def client(server, db_provisioning):
    client = dci_client.DCIClient(
        end_point='http://dci_server.com/api',
        login='admin', password='admin'
    )
    flask_adapter = utils.FlaskHTTPAdapter(server.test_client())
    client.s.mount('http://dci_server.com', flask_adapter)
    return client


@pytest.fixture
def http_session(server, db_provisioning):
    session = commands._get_http_session('http://dci_server.com',
                                         'admin', 'admin')
    flask_adapter = utils.FlaskHTTPAdapter(server.test_client())
    session.mount('http://dci_server.com', flask_adapter)
    return session


@pytest.fixture
def runner(monkeypatch, http_session):
    monkeypatch.setattr(commands, '_get_http_session', lambda *_: http_session)
    runner = click.testing.CliRunner(env={'DCI_LOGIN': '', 'DCI_PASSWORD': '',
                                          'DCI_CLI_OUTPUT_FORMAT': 'json'})
    runner.invoke = functools.partial(runner.invoke, shell.main)
    return runner


@pytest.fixture
def team_id(http_session):
    return team.Team(http_session).create(name='tname').json()['team']['id']


@pytest.fixture
def job_id(http_session):
    my_team = team.Team(http_session).create(name='tname').json()['team']
    my_remoteci = remoteci.RemoteCI(http_session).create(
        name='tname', team_id=my_team['id'],
        data={'remoteci': 'remoteci'}).json()
    my_remoteci_id = my_remoteci['remoteci']['id']
    my_test = test.Test(http_session).create(
        name='tname', data={'test': 'test'}).json()
    my_test_id = my_test['test']['id']
    l_jobdefinition = jobdefinition.JobDefinition(http_session)
    my_jobdefinition = l_jobdefinition.create(
        name='tname', test_id=my_test_id).json()
    my_component = component.Component(http_session).create(
        name='hihi', type='git_review', data={'component': 'component'}).json()
    my_component_id = my_component['component']['id']
    l_jobdefinition.add_component(my_jobdefinition['jobdefinition']['id'],
                                  my_component_id)
    my_job = job.Job(http_session).schedule(my_remoteci_id).json()
    return my_job['job']['id']
