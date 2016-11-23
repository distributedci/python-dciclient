# -*- encoding: utf-8 -*-
#
# Copyright 2016 Red Hat, Inc.
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


def test_prettytable_output(runner):
    topic = runner.invoke(['topic-create', '--name', 'osp'])['topic']
    result = runner.invoke_raw([
        '--format', 'table', 'topic-show', topic['id']])

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

    expected_data = (topic['id'], topic['name'],
                     topic['etag'], topic['created_at'],
                     topic['updated_at'])

    assert header == ('| id | name | etag '
                      '| created_at | updated_at |')

    assert data == ('| %s | %s | %s | %s | %s |' % expected_data)


def test_list(runner):
    runner.invoke(['topic-create', '--name', 'osp'])
    runner.invoke(['topic-create', '--name', 'ovirt'])
    topics = runner.invoke(['topic-list'])['topics']

    assert len(topics) == 2
    assert topics[0]['name'] == 'osp'
    assert topics[1]['name'] == 'ovirt'


def test_create(runner):
    topic = runner.invoke(['topic-create', '--name', 'osp'])['topic']
    assert topic['name'] == 'osp'


def test_delete(runner):
    topic = runner.invoke(['topic-create', '--name', 'osp'])['topic']
    result = runner.invoke(['topic-delete', topic['id']])

    assert result['message'] == 'Topic deleted.'


def test_show(runner):
    topic = runner.invoke(['topic-create', '--name', 'osp'])['topic']
    topic = runner.invoke(['topic-show', topic['id']])['topic']

    assert topic['name'] == 'osp'


def test_attach_team(runner):
    team = runner.invoke(['team-create', '--name', 'foo'])['team']
    assert team['name'] == 'foo'

    topic = runner.invoke(['topic-create', '--name', 'osp'])['topic']
    assert topic['name'] == 'osp'

    topic_team = runner.invoke(['topic-attach-team', topic['id'],
                                '--team_id', team['id']])
    assert topic_team['team_id'] == team['id']
    assert topic_team['topic_id'] == topic['id']


def test_list_team(runner):
    team = runner.invoke(['team-create', '--name', 'foo'])['team']
    assert team['name'] == 'foo'

    topic = runner.invoke(['topic-create', '--name', 'osp'])['topic']
    assert topic['name'] == 'osp'

    topic_team = runner.invoke(['topic-attach-team', topic['id'],
                                '--team_id', team['id']])
    assert topic_team['team_id'] == team['id']
    assert topic_team['topic_id'] == topic['id']

    result = runner.invoke(['topic-list-team', topic['id']])['teams']
    assert len(result) == 1
    assert result[0]['name'] == 'foo'


def test_unattach_team(runner):
    team = runner.invoke(['team-create', '--name', 'foo'])['team']
    assert team['name'] == 'foo'

    topic = runner.invoke(['topic-create', '--name', 'osp'])['topic']
    assert topic['name'] == 'osp'

    topic_team = runner.invoke(['topic-attach-team', topic['id'],
                                '--team_id', team['id']])
    assert topic_team['team_id'] == team['id']
    assert topic_team['topic_id'] == topic['id']

    result = runner.invoke(['topic-list-team', topic['id']])['teams']
    assert len(result) == 1
    assert result[0]['name'] == 'foo'

    topic_team = runner.invoke(['topic-unattach-team', topic['id'],
                                '--team_id', team['id']])

    teams = runner.invoke(['topic-list-team', topic['id']])['teams']
    assert len(teams) == 0
