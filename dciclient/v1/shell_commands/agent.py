# -*- encoding: utf-8 -*-
#
# Copyright 2017 Red Hat, Inc.
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

from pprint import pprint


def _available_agents():
    "Dummy agents"

    return (
        "ocp",
        "rhel",
        "osp",
    )


def _get_agent_queue():
    "Dummy queue contents, probably want to slice this by agent type"

    return [
        {"agent": "rhel", "parameters": {}},
        {"agent": "ocp", "parameters": {}},
        {"agent": "ocp", "parameters": {}},
        {"agent": "ocp", "parameters": {}},
        {"agent": "osp", "parameters": {}},
    ]


def list(context, args):
    "Lists all configured clients"

    print("Here's a list of all configured DCI agents on this system:")
    pprint(_available_agents())


def run(context, args):
    "Performs an agent run NOW"

    agent = args.agent

    if agent not in _available_agents():
        raise KeyError("Agent {} is not configured on the system".format(agent))

    print("Running agent {}...".format(agent))


def queue(context, args):
    "Queues an agent run"

    agent = args.agent

    if agent not in _available_agents():
        raise KeyError("Agent {} is not configured on the system".format(agent))

    print("Pushing {} agent run to the end of the queue...".format(agent))


def inspect(context, args):
    "Inspects the agent queue"

    print("Queue:")
    queue = _get_agent_queue()
    for pos, item in enumerate(queue):
        print("{}: {}".format(pos, item))


def cancel(context, args):
    "Expunges a queued agent run"

    queue = _get_agent_queue()
    print("Removing item {} from the queue".format(args.item))
    queue.pop(args.item)
    print("Resulting queue:")
    for pos, item in enumerate(queue):
        print("{}: {}".format(pos, item))


def kill(context, args):
    "Kills the currently running agent"

    print("Killing agent run...")
