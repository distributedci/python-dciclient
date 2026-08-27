# -*- encoding: utf-8 -*-
#
# Copyright 2026 Red Hat, Inc.
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

import logging
import os
import re
from io import StringIO

logger = logging.getLogger(__name__)

REDACT_REPLACEMENT = "***REDACTED***"

DEFAULT_REDACT_PATTERNS = [
    # GitHub tokens
    # https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-authentication-to-github#githubs-token-formats
    (r"gh[hopru]_[a-zA-Z0-9]{36}", REDACT_REPLACEMENT),
    (r"github_pat_[a-zA-Z0-9_]{82}", REDACT_REPLACEMENT),
    (r"ghs_[A-Za-z0-9\.\-_]{36,}", REDACT_REPLACEMENT),
    # DCI credentials
    (r"remoteci/[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}", REDACT_REPLACEMENT),
    (r"DCI\.[a-zA-Z0-9]{60}", REDACT_REPLACEMENT),
    # Pull secrets (JSON and YAML)
    (r'("auth"\s*:\s*")[^"]*(")', r"\1" + REDACT_REPLACEMENT + r"\2"),
    (r"(auth:\s+)\S+", r"\1" + REDACT_REPLACEMENT),
]


def should_redact(redact=False):
    """Determine whether redaction should be applied.

    The DCI_REDACT environment variable takes precedence if set.
    Otherwise the redact parameter value is used.
    """
    env_val = os.environ.get("DCI_REDACT")
    if env_val is not None:
        return env_val.lower() in ("1", "true", "yes")
    return redact


def get_patterns():
    """Return a list of compiled patterns to redact.

    When DCI_REDACT_PATTERNS is set, its colon-separated values are used
    as patterns (each replaced with REDACT_REPLACEMENT). Custom patterns
    replace defaults entirely.
    """
    env_val = os.environ.get("DCI_REDACT_PATTERNS")
    if env_val is not None:
        raw_patterns = [(p, REDACT_REPLACEMENT) for p in env_val.split(":") if p]
    else:
        raw_patterns = DEFAULT_REDACT_PATTERNS

    compiled = []
    for pattern_str, replacement in raw_patterns:
        try:
            compiled.append((re.compile(pattern_str, re.MULTILINE), replacement))
        except re.error as e:
            logger.warning("Invalid redact pattern %r: %s", pattern_str, e)
    return compiled


def redact_stream(src, dst):
    """Redact sensitive patterns from src writing the result to dst.

    Reads line by line from src and applies redaction patterns to each
    line before writing to dst. Both src and dst must be text-mode
    file-like objects.
    """
    patterns = get_patterns()
    for line in src:
        for pattern, replacement in patterns:
            line = pattern.sub(replacement, line)
        dst.write(line)


def redact_file(input_path, output_path):
    """Redact sensitive patterns from a file writing the result to another file.

    Opens input_path in text mode tolerating non-UTF-8 content, like binary
    fragments in log files.
    """
    with open(input_path, "r", encoding="utf-8", errors="ignore") as src, \
         open(output_path, "w", encoding="utf-8") as dst:
        redact_stream(src, dst)


def redact_content(content):
    """Redact sensitive patterns from a string.

    Returns a new string with all matching patterns replaced.
    """
    src = StringIO(content)
    dst = StringIO()
    redact_stream(src, dst)
    return dst.getvalue()
