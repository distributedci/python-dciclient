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

from dciclient.v1.handlers import job


def test_get_full_data(job_id, http_session):
    l_job = job.Job(http_session)
    full_data_job = l_job.get_full_data(job_id)
    assert full_data_job['remoteci'] == {'remoteci': 'remoteci'}
    assert full_data_job['test'] == {'test': 'test'}
    assert full_data_job['components'] == [{'component': 'component'}]
