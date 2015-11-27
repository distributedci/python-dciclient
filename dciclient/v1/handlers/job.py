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


class Job(dcibaseresource.DCIBaseResource):
    ENDPOINT_URI = 'jobs'

    def __init__(self, dci_client):
        super(Job, self).__init__(dci_client, self.ENDPOINT_URI)

    def create(self, recheck, remoteci_id, team_id, jobdefinition_id=None):
        return super(Job, self).create(recheck=recheck,
                                       remoteci_id=remoteci_id,
                                       team_id=team_id,
                                       jobdefinition_id=jobdefinition_id)

    def show(self, id):
        return super(Job, self).show(id=id)
