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

from dciclient.v1.api import job


def test_get_full_data(job_id, dci_context):
    full_data_job = job.get_full_data(dci_context, job_id)
    assert full_data_job['remoteci']['data'] == {'remoteci': 'remoteci'}
    assert full_data_job['jobdefinition']['name'] == 'tname'
    assert full_data_job['components'][0]['name'] == 'hihi'
