# -*- encoding: utf-8 -*-
#
# Copyright Red Hat, Inc.
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

import pytest
import responses

from dciclient.v1.api.context import DciContext
from dciclient.v1.shell_commands.cli import parse_arguments
from dciclient.v1.shell_commands.runner import run


@pytest.mark.parametrize(
    "params",
    [
        ["team-attach-user"],
        ["team-attach-user", "t1"],
        ["team-attach-user", "--user-id", "u1"],
    ],
)
def test_attach_user_requires_team_and_user_ids(params):
    with pytest.raises(SystemExit) as exc:
        parse_arguments(params)
    assert exc.value.code == 2


@responses.activate
def test_attach_user_sends_ids_in_url_without_body():
    context = DciContext("http://localhost", "admin", "admin")
    responses.post("http://localhost/api/v1/teams/t1/users/u1", status=201)
    args = parse_arguments(["team-attach-user", "t1", "--user-id", "u1"])

    result = run(context, args)

    assert result.status_code == 201
    assert result.content == b""
    assert len(responses.calls) == 1
    request = responses.calls[0].request
    assert request.body is None
    assert "If-match" not in request.headers


@pytest.mark.parametrize("status_code", [401, 404, 409])
@responses.activate
def test_attach_user_preserves_server_errors(status_code):
    context = DciContext("http://localhost", "admin", "admin")
    error = {"message": "Cannot attach user"}
    responses.post(
        "http://localhost/api/v1/teams/t1/users/u1",
        status=status_code,
        json=error,
    )
    args = parse_arguments(["team-attach-user", "t1", "--user-id", "u1"])

    result = run(context, args)

    assert result.status_code == status_code
    assert result.json() == error
