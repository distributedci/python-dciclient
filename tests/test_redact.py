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

from io import StringIO

from dciclient.v1.api import redact

REDACTED = redact.REDACT_REPLACEMENT


class TestShouldRedact:
    def test_default(self):
        assert redact.should_redact() is False

    def test_explicit_true(self):
        assert redact.should_redact(redact=True) is True

    def test_explicit_false(self):
        assert redact.should_redact(redact=False) is False

    def test_env_var_true_overrides_param(self, monkeypatch):
        monkeypatch.setenv("DCI_REDACT", "1")
        assert redact.should_redact(redact=False) is True

    def test_env_var_false_overrides_param(self, monkeypatch):
        monkeypatch.setenv("DCI_REDACT", "false")
        assert redact.should_redact(redact=True) is False

    def test_env_var_zero(self, monkeypatch):
        monkeypatch.setenv("DCI_REDACT", "0")
        assert redact.should_redact() is False

    def test_env_var_no(self, monkeypatch):
        monkeypatch.setenv("DCI_REDACT", "no")
        assert redact.should_redact() is False

    def test_env_var_yes(self, monkeypatch):
        monkeypatch.setenv("DCI_REDACT", "yes")
        assert redact.should_redact() is True


class TestGetPatterns:
    def test_returns_default_patterns(self):
        patterns = redact.get_patterns()
        assert len(patterns) == len(redact.DEFAULT_REDACT_PATTERNS)

    def test_env_patterns_override_defaults(self, monkeypatch):
        monkeypatch.setenv("DCI_REDACT_PATTERNS", r"secret_\d+:token_\w+")
        patterns = redact.get_patterns()
        assert len(patterns) == 2

    def test_env_empty_segments_ignored(self, monkeypatch):
        monkeypatch.setenv("DCI_REDACT_PATTERNS", r"secret_\d+::token_\w+:")
        patterns = redact.get_patterns()
        assert len(patterns) == 2

    def test_invalid_pattern_warns(self, monkeypatch, caplog):
        monkeypatch.setenv("DCI_REDACT_PATTERNS", "[invalid")
        import logging

        with caplog.at_level(logging.WARNING):
            patterns = redact.get_patterns()
        assert len(patterns) == 0
        assert "Invalid redact pattern" in caplog.text


class TestRedactStream:
    def test_redacts_token(self):
        token = "ghp_" + "a" * 36
        src = StringIO("token=%s\n" % token)
        dst = StringIO()
        redact.redact_stream(src, dst)
        assert token not in dst.getvalue()
        assert REDACTED in dst.getvalue()

    def test_no_match_unchanged(self):
        src = StringIO("nothing sensitive here\n")
        dst = StringIO()
        redact.redact_stream(src, dst)
        assert dst.getvalue() == "nothing sensitive here\n"

    def test_empty_input(self):
        src = StringIO("")
        dst = StringIO()
        redact.redact_stream(src, dst)
        assert dst.getvalue() == ""

    def test_multiple_lines(self):
        token = "ghp_" + "a" * 36
        src = StringIO("line1\ntoken=%s\nline3\n" % token)
        dst = StringIO()
        redact.redact_stream(src, dst)
        output = dst.getvalue()
        assert token not in output
        assert "line1\n" in output
        assert "\nline3\n" in output

    def test_multiple_tokens_across_lines(self):
        token1 = "ghp_" + "a" * 36
        token2 = "ghp_" + "b" * 36
        src = StringIO("%s\n%s\n" % (token1, token2))
        dst = StringIO()
        redact.redact_stream(src, dst)
        output = dst.getvalue()
        assert token1 not in output
        assert token2 not in output

    def test_custom_patterns(self, monkeypatch):
        monkeypatch.setenv("DCI_REDACT_PATTERNS", "PASSWORD=\\S+:SECRET=\\S+")
        src = StringIO("PASSWORD=hunter2 SECRET=monkey123\n")
        dst = StringIO()
        redact.redact_stream(src, dst)
        output = dst.getvalue()
        assert "hunter2" not in output
        assert "monkey123" not in output
        assert REDACTED in output


class TestRedactFile:
    def test_redacts_token(self, tmp_path):
        token = "ghp_" + "a" * 36
        input_file = tmp_path / "input.log"
        output_file = tmp_path / "output.log"
        input_file.write_text("token=%s\n" % token)
        redact.redact_file(str(input_file), str(output_file))
        result = output_file.read_text()
        assert token not in result
        assert REDACTED in result

    def test_empty_file(self, tmp_path):
        input_file = tmp_path / "input.log"
        output_file = tmp_path / "output.log"
        input_file.write_text("")
        redact.redact_file(str(input_file), str(output_file))
        assert output_file.read_text() == ""

    def test_multiple_tokens_across_lines(self, tmp_path):
        token1 = "ghp_" + "a" * 36
        token2 = "ghp_" + "b" * 36
        input_file = tmp_path / "input.log"
        output_file = tmp_path / "output.log"
        input_file.write_text("%s\n%s\n" % (token1, token2))
        redact.redact_file(str(input_file), str(output_file))
        result = output_file.read_text()
        assert token1 not in result
        assert token2 not in result

    def test_binary_tolerant(self, tmp_path):
        input_file = tmp_path / "input.log"
        output_file = tmp_path / "output.log"
        input_file.write_bytes("valid line\n\x80\x81\xff\xfe\nmore text\n".encode("latin-1"))
        redact.redact_file(str(input_file), str(output_file))
        result = output_file.read_text()
        assert "valid line" in result
        assert "more text" in result

    def test_no_match_unchanged(self, tmp_path):
        input_file = tmp_path / "input.log"
        output_file = tmp_path / "output.log"
        input_file.write_text("nothing sensitive here\n")
        redact.redact_file(str(input_file), str(output_file))
        assert output_file.read_text() == "nothing sensitive here\n"


class TestRedactContent:
    def test_redact_ghp_token(self):
        token = "ghp_" + "a" * 36
        result = redact.redact_content("token: %s end" % token)
        assert token not in result
        assert REDACTED in result
        assert result == "token: %s end" % REDACTED

    def test_redact_github_pat_token(self):
        token = "github_pat_" + "A" * 82
        result = redact.redact_content("auth=%s" % token)
        assert token not in result
        assert REDACTED in result

    def test_redact_gho_token(self):
        token = "gho_" + "x" * 36
        result = redact.redact_content("GITHUB_TOKEN=%s" % token)
        assert token not in result
        assert REDACTED in result

    def test_redact_remoteci_uuid(self):
        remoteci = "remoteci/12345678-1234-1234-1234-123456789abc"
        result = redact.redact_content("client_id=%s" % remoteci)
        assert remoteci not in result
        assert REDACTED in result

    def test_redact_dci_secret(self):
        secret = "DCI." + "a" * 60
        result = redact.redact_content("api_secret=%s" % secret)
        assert secret not in result
        assert REDACTED in result

    def test_redact_pull_secret_json(self):
        content = '{"auths": {"registry.example.com": {"auth": "dXNlcjpwYXNz"}}}'
        result = redact.redact_content(content)
        assert "dXNlcjpwYXNz" not in result
        assert '"auth": "%s"' % REDACTED in result

    def test_redact_pull_secret_json_with_spaces(self):
        result = redact.redact_content('"auth" : "secretvalue"')
        assert "secretvalue" not in result
        assert REDACTED in result

    def test_redact_pull_secret_yaml(self):
        result = redact.redact_content("auth: mysecrettoken")
        assert "mysecrettoken" not in result
        assert "auth: %s" % REDACTED in result

    def test_returns_str(self):
        token = "ghp_" + "a" * 36
        result = redact.redact_content("token: %s" % token)
        assert isinstance(result, str)

    def test_no_match_unchanged(self):
        assert redact.redact_content("nothing sensitive here") == "nothing sensitive here"

    def test_empty_string(self):
        assert redact.redact_content("") == ""

    def test_multiple_matches(self):
        token1 = "ghp_" + "a" * 36
        token2 = "ghp_" + "b" * 36
        result = redact.redact_content("%s and %s" % (token1, token2))
        assert token1 not in result
        assert token2 not in result

    def test_multiline_content(self):
        token = "ghp_" + "c" * 36
        result = redact.redact_content("line1\ntoken=%s\nline3" % token)
        assert token not in result
        assert "line1\n" in result
        assert "\nline3" in result

    def test_custom_patterns(self, monkeypatch):
        monkeypatch.setenv("DCI_REDACT_PATTERNS", "PASSWORD=\\S+:SECRET=\\S+")
        result = redact.redact_content("PASSWORD=hunter2 something SECRET=monkey123 else")
        assert "hunter2" not in result
        assert "monkey123" not in result
        assert REDACTED in result
