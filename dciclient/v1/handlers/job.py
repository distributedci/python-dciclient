# -*- encoding: utf-8 -*-
#
# Copyright 2015 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from dciclient.v1.handlers import dcibaseresource
from dciclient.v1.handlers import jobdefinition


class Job(dcibaseresource.DCIBaseResource):
    ENDPOINT_URI = 'jobs'
    TABLE_HEADERS = ['id', 'recheck', 'jobdefinition_id', 'remoteci_id',
                     'team_id', 'etag', 'created_at', 'updated_at']

    def __init__(self, dci_client):
        super(Job, self).__init__(dci_client, self.ENDPOINT_URI)
        self._dci_client = dci_client

    def create(self, recheck, remoteci_id, team_id, jobdefinition_id=None):
        return super(Job, self).create(recheck=recheck,
                                       remoteci_id=remoteci_id,
                                       team_id=team_id,
                                       jobdefinition_id=jobdefinition_id)

    def schedule(self, remoteci_id):
        data_json = {'remoteci_id': remoteci_id}
        return self._s.post('%s/schedule' % self._end_point_with_uri,
                            json=data_json)

    def get(self, id, where=None, embed=None):
        return super(Job, self).get(id=id, where=where, embed=embed)

    def get_full_data(self, id):
        # Get the job with embed on test and remoteci
        embed = 'jobdefinition,jobdefinition.test,remoteci'
        job = self.get(id=id, embed=embed).json()['job']
        # Get the components of the jobdefinition
        l_jobdefinition = jobdefinition.JobDefinition(self._dci_client)
        jobdefinition_components = l_jobdefinition.get_components(
            job['jobdefinition']['id']).json()['components']

        # Aggregate the data of each resource
        full_data = {'remoteci': job['remoteci']['data'],
                     'test': job['jobdefinition']['test']['data'],
                     'components': []}

        for component in jobdefinition_components:
            full_data['components'].append(component['data'])

        return full_data
