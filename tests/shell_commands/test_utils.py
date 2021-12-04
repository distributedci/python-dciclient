# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 Red Hat, Inc.
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

from dciclient.v1 import utils


class TestUtils(object):
    def test_flatten(self):
        s = {"jim": 123, "a": {"b": {"c": {"d": "bob"}}}, "rob": 34}
        r = utils.flatten(s)
        r.sort()
        assert r == ["a.b.c.d=bob", "jim=123", "rob=34"]


def test_escape_invalid_char():
    assert utils.is_valid_file_name("@\r!.log") is False
    assert utils.is_valid_file_name("attack)!\r.log") is False
    assert utils.is_valid_file_name("NASTY!\r.log") is False
    assert utils.is_valid_file_name("changed.\r.log") is False
    assert (
        utils.is_valid_file_name(
            "SHA256:kUcmk05yBNUvit53RUelIJwCBczNvCeoFVBZ07VU5sE.\r.log"
        )
        is False
    )
    assert utils.is_valid_file_name("administrator.\r.log") is False
    assert utils.is_valid_file_name("message.\r.log") is False
    assert utils.is_valid_file_name("changed.\r.log") is False
    assert utils.is_valid_file_name("@\n!.log") is False
    assert utils.is_valid_file_name("@\t!.log") is False
    assert utils.is_valid_file_name("..") is False
    assert utils.is_valid_file_name("Ansible..log")
