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

from __future__ import unicode_literals
import json


def test_prettytable_output(runner):
    result = runner.invoke(['team-create', '--name', 'foo'])
    team = json.loads(result.output)['team']
    result = runner.invoke(['remoteci-create', '--name', 'foo', '--team_id',
                            team['id']])
    remoteci = json.loads(result.output)['remoteci']

    result = runner.invoke(['--format', 'table', 'remoteci-show', '--id',
                            remoteci['id']])

    output = result.output.split('\n')
    # NOTE(spredzy) : The expected output for a table format looks like the
    #                 following :
    #
    # +------------
    # |  id | name
    # +------------
    # | id1 | name1
    # | id2 | name2
    # | id3 | name3
    # +------------
    #
    # The header variable below represents the header data, when more than one
    # space is located between the string and the '|' space number is shrink to
    # one ( this is what ' '.join(string.split()) does
    #
    # The data variable below represents the actual data, when more than one
    # space is located between the string and the '|' space number is shrink to
    # one ( this is what ' '.join(string.split()) does
    header = ' '.join(output[1].split())
    data = ' '.join(output[3].split())

    expected_data = (remoteci['id'], remoteci['name'], remoteci['team_id'],
                     remoteci['etag'], remoteci['created_at'],
                     remoteci['updated_at'])

    assert header == ('| id | name | data | team_id | etag | created_at '
                      '| updated_at |')

    assert data == '| %s | %s | {} | %s | %s | %s | %s |' % expected_data


def test_list(runner):
    result = runner.invoke(['team-create', '--name', 'foo'])
    team = json.loads(result.output)['team']

    runner.invoke(['remoteci-create', '--name', 'foo', '--team_id',
                   team['id']])
    runner.invoke(['remoteci-create', '--name', 'bar', '--team_id',
                   team['id']])
    result = runner.invoke(['remoteci-list'])
    remotecis = json.loads(result.output)['remotecis']

    assert len(remotecis) == 2
    assert remotecis[0]['name'] == 'foo'
    assert remotecis[1]['name'] == 'bar'


def test_create(runner):
    result = runner.invoke(['team-create', '--name', 'foo'])
    team = json.loads(result.output)['team']
    result = runner.invoke(['remoteci-create', '--name', 'foo', '--team_id',
                            team['id']])
    remoteci = json.loads(result.output)['remoteci']
    assert remoteci['name'] == 'foo'


def test_update(runner):
    result = runner.invoke(['team-create', '--name', 'foo'])
    team = json.loads(result.output)['team']
    result = runner.invoke(['remoteci-create', '--name', 'foo', '--team_id',
                            team['id']])
    remoteci = json.loads(result.output)['remoteci']

    result = runner.invoke(['remoteci-update', '--id', remoteci['id'],
                            '--etag', remoteci['etag'], '--name', 'bar'])
    result = json.loads(result.output)

    assert result['message'] == 'Remote CI updated.'
    assert result['name'] == 'bar'


def test_delete(runner):
    result = runner.invoke(['team-create', '--name', 'foo'])
    team = json.loads(result.output)['team']

    result = runner.invoke(['remoteci-create', '--name', 'foo', '--team_id',
                            team['id']])
    remoteci = json.loads(result.output)['remoteci']

    result = runner.invoke(['remoteci-delete', '--id', remoteci['id'],
                            '--etag', remoteci['etag']])
    result = json.loads(result.output)

    assert result['message'] == 'Remote CI deleted.'


def test_show(runner):
    result = runner.invoke(['team-create', '--name', 'foo'])
    team = json.loads(result.output)['team']
    result = runner.invoke(['remoteci-create', '--name', 'foo', '--team_id',
                            team['id']])
    remoteci = json.loads(result.output)['remoteci']

    result = runner.invoke(['remoteci-show', '--id', remoteci['id']])
    remoteci = json.loads(result.output)['remoteci']

    assert remoteci['name'] == 'foo'
