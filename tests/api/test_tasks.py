# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Red Hat, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from dciclient.v1.api import task as api_task


def test_create_task(dci_context, jobstate_id, tmp_path):
    name = "TASK: [ Print DCI test ♥] **************************************"
    duration = 123
    status = "failed"
    content = 'ok: [127.0.0.1] => {     "msg": "DCI test ♥" }'
    mime_type = "text/plain"
    task = {
        "jobstate_id": jobstate_id,
        "name": name,
        "status": status,
        "duration": duration,
        "content": content,
        "mime_type": mime_type,
    }
    # create
    task = api_task.create(dci_context, task)
    assert task["name"] == name
    assert task["duration"] == 123
    assert task["status"] == "failed"

    # get content
    assert api_task.content(dci_context, task["id"]) == content

    # head
    headers = api_task.head(dci_context, task["id"])
    assert headers["Content-Type"] == mime_type

    # download
    target = tmp_path / "task.txt"
    api_task.download(dci_context, task["id"], str(target))
    with open(target, "rb") as f:
        data = f.read()
    assert data == content.encode("utf-8")
