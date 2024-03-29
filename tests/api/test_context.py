# -*- coding: utf-8 -*-
#
# Copyright (C) 2017-2022 Red Hat, Inc
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
# under the License.o

from datetime import datetime, timedelta
try:
    from datetime.timezone import utc as tzutc
except:
    from dateutil.tz import UTC as tzutc
from dciclient.v1.api import topic as api_topic
from mock import patch
import pytest


def fakeServerTime():
    t = datetime.now(tzutc) - timedelta(minutes=10)
    return t.strftime("%a, %d %b %Y %X %Z")


@patch("dciclient.v1.api.context._extract_date_from_headers",
       return_value=fakeServerTime())
def test_list_topics_with_unsynced_time(mock_extract_date, dci_context):
    with pytest.raises(SystemExit) as e:
        api_topic.list(dci_context)
        assert mock_extract_date.called
        assert e.msg == ("ERROR: Your system and DCI servers clocks are "
                         "unsynchronized. API results might be incorrect. "
                         "Please check your system clock.")
