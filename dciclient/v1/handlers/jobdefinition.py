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


class JobDefinition(dcibaseresource.DCIBaseResource):
    ENDPOINT_URI = 'jobdefinitions'
    TABLE_HEADERS = ['id', 'name', 'priority', 'test_id', 'etag', 'created_at',
                     'updated_at']

    def __init__(self, session):
        super(JobDefinition, self).__init__(session, self.ENDPOINT_URI)

    def create(self, name, test_id, priority=None):
        return super(JobDefinition, self).create(name=name, test_id=test_id,
                                                 priority=priority)

    def delete(self, id, etag):
        return super(JobDefinition, self).delete(id=id, etag=etag)

    def get(self, id, where=None, embed=None):
        return super(JobDefinition, self).get(id=id, where=where, embed=embed)

    def add_component(self, id, component_id):
        url = '%s/%s/components' % (self._end_point_with_uri, id)
        return self._s.post(url, json={'component_id': component_id})

    def get_components(self, id):
        url = '%s/%s/components' % (self._end_point_with_uri, id)
        return self._s.get(url)
