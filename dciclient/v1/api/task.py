# -*- encoding: utf-8 -*-
#
# Copyright 2015-2016 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this task except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import requests

from dciclient.v1.api import base


TASK_STATUSES = ["completed", "failed", "skipped", "ignored"]


def ensure_bytes(data):
    if isinstance(data, bytes):
        return data
    return data.encode("utf-8")


def create(context, task):
    jobstate_id = task["jobstate_id"]
    name = task["name"]
    status = task.get("status", "completed")
    duration = task.get("duration", 0)
    content = task.get("content", "")
    mime_type = task.get("mime_type", "text/plain")

    if status not in TASK_STATUSES:
        raise Exception(
            f"Status {status} is invalid. Should one of {','.join(TASK_STATUSES)}"
        )

    data = {
        "name": name,
        "jobstate_id": jobstate_id,
        "duration": duration,
        "status": status,
    }
    create_task = context.session.post(f"{context.dci_cs_api_v2}/tasks", json=data)
    task = create_task.json()["task"]
    upload_task_content = requests.put(
        task["upload_url"],
        data=ensure_bytes(content),
        headers={"Content-Type": mime_type},
    )
    upload_task_content.raise_for_status()
    return task


def get(context, id, **kwargs):
    return base.get(context, "tasks", id=id, **kwargs)


def content(context, id):
    uri = f"{context.dci_cs_api_v2}/tasks/{id}/content"
    return context.session.get(uri).content.decode("utf-8")


def head(context, id):
    uri = f"{context.dci_cs_api_v2}/tasks/{id}/content"
    response = context.session.head(uri)
    location = response.headers.get("Location")
    head_response = requests.head(location)
    head_response.raise_for_status()
    return head_response.headers


def download(context, id, file_path):
    uri = f"{context.dci_cs_api_v2}/tasks/{id}/content"
    base.download(context, uri, file_path)
