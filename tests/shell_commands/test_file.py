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
from __future__ import unicode_literals
import pytest
from dciclient.v1.api import job as api_job
from dciclient.v1.api import file as api_file
from dciclient.v1.api import topic as api_topic


def test_show(runner, file_id):
    result = runner.invoke_raw(["file-show", file_id])
    assert "testsuite errors" in result.text


def test_list(runner, job_id):
    files = runner.invoke(["file-list", job_id])["files"]
    assert len(files)
    assert "res_junit.xml" in [i["name"] for i in files]


def test_delete(runner, file_id):
    result = runner.invoke_raw(["file-delete", file_id])
    assert result.status_code == 204


def test_where_on_list(runner, job_id):
    files = runner.invoke(["file-list", job_id, "--where", "size:785"])['files']
    assert len(files) == 1
    assert files[0]['size'] == 785


def test_nrt_create_file_with_invalid_return_character(
    dci_context,
    dci_context_remoteci,
    team_user_id,
    remoteci_id,
    topic_id,
    components_ids,
):
    api_topic.attach_team(dci_context, topic_id, team_user_id)
    request = api_job.schedule(dci_context_remoteci, topic_id).json()
    job_id = request["job"]["id"]
    with pytest.raises(Exception) as execinfo:
        request = api_file.create(
            dci_context_remoteci,
            name="@\r!.log",
            content="content",
            mime="text/plain",
            job_id=job_id,
        )
    assert execinfo.value.args[0] == "Invalid file name"
    request = api_file.create(
        dci_context_remoteci,
        name="Ansible..log",
        content="content",
        mime="text/plain",
        job_id=job_id,
    )
    file = request.json()["file"]
    assert request.status_code == 201
    assert file["name"] == "Ansible..log"
