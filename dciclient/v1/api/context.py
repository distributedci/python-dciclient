# Copyright 2015-2016, 2022 Red Hat, Inc.
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
import os.path

try:
    from urlparse import parse_qsl
    from urlparse import urlparse
except ImportError:
    from urllib.parse import parse_qsl
    from urllib.parse import urlparse
import requests
from requests.adapters import HTTPAdapter
from requests.auth import AuthBase
from urllib3.util.retry import Retry

from dciauth.v2.headers import generate_headers
from dciclient import version
from dciclient.v1.api.token_storage import TokenStorage

logger = logging.getLogger(__name__)


class DciContextBase(object):
    API_VERSION = "api/v1"

    def __init__(self, dci_cs_url, max_retries=10, user_agent=None):
        self.session = self._build_http_session(user_agent, max_retries)
        self.dci_cs_api = "%s/%s" % (dci_cs_url, DciContext.API_VERSION)
        self.last_job_id = None

    @staticmethod
    def _build_http_session(user_agent, max_retries):
        session = requests.Session()
        session.headers.setdefault("Content-Type", "application/json")
        if not user_agent:
            user_agent = "python-dciclient_%s" % version.__version__
        session.headers["User-Agent"] = user_agent
        session.headers["Client-Version"] = "python-dciclient_%s" % version.__version__
        retries = Retry(
            total=max_retries,
            backoff_factor=0.2,
            status_forcelist=(413, 429, 500, 502, 503, 504),
            raise_on_status=False,
        )
        session.mount("http://", HTTPAdapter(max_retries=retries))
        session.mount("https://", HTTPAdapter(max_retries=retries))

        return session


class DciContext(DciContextBase):
    """
    DEPRECATED: This class now uses JWT authentication instead of Basic auth.
    Consider using JWTContext directly via build_jwt_context() or login via dcictl login.
    """
    def __init__(self, dci_cs_url, login, password, max_retries=10, user_agent=None):
        logger.warning(
            "DciContext is deprecated and now uses JWT authentication instead of Basic auth. "
            "Consider using 'dcictl login' and JWTContext, or use build_jwt_context()."
        )
        super(DciContext, self).__init__(
            dci_cs_url.rstrip("/"), max_retries, user_agent
        )
        self.login = login

        # Login via JWT endpoint to get tokens
        login_url = "%s/%s/auth/login" % (dci_cs_url.rstrip("/"), DciContext.API_VERSION)
        response = requests.post(
            login_url,
            json={"email": login, "password": password},
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()

        tokens = response.json()

        # Create in-memory token storage (token_file=False means in-memory only)
        token_storage = TokenStorage(token_file=False)
        token_storage.save_tokens(tokens["access_token"], tokens["refresh_token"])

        # Use JWT authentication
        self.session.auth = JWTBearerAuth(dci_cs_url.rstrip("/"), token_storage)


def build_dci_context(
    dci_cs_url=None, dci_login=None, dci_password=None, user_agent=None, max_retries=10
):
    dci_cs_url = dci_cs_url or os.environ.get("DCI_CS_URL", "")
    dci_login = dci_login or os.environ.get("DCI_LOGIN", "")
    dci_password = dci_password or os.environ.get("DCI_PASSWORD", "")

    if not dci_cs_url or not dci_login or not dci_password:
        msg = (
            "Environment variables required: DCI_CS_URL=%s, "
            "DCI_LOGIN=%s, DCI_PASSWORD=%s" % (dci_cs_url, dci_login, dci_password)
        )
        raise Exception(msg)

    return DciContext(
        dci_cs_url.rstrip("/"),
        dci_login,
        dci_password,
        user_agent=user_agent,
        max_retries=max_retries,
    )


class DciSignatureAuth(AuthBase):
    """Signs the request for DCI API with signature authentication"""

    def __init__(self, client_id, api_secret):
        self.client_type, self.client_id = self.get_client_info(client_id)
        self.api_secret = api_secret

    @staticmethod
    def get_client_info(client_id):
        if client_id.find("/") == -1:
            return ["remoteci", client_id]
        return client_id.split("/")[:2]

    def __call__(self, r):
        url = urlparse(r.url)
        r.headers.update(
            generate_headers(
                {
                    "method": r.method,
                    "endpoint": url.path,
                    "params": dict(parse_qsl(url.query)),
                    "host": url.netloc,
                    "data": self.get_body(r.body),
                },
                {
                    "access_key": "%s/%s" % (self.client_type, self.client_id),
                    "secret_key": self.api_secret,
                },
            )
        )
        return r

    def get_body(self, body):
        if hasattr(body, "read"):
            c = body.read()
            body.seek(0)
            return c
        return body


class DciSignatureContext(DciContextBase):
    def __init__(
        self, dci_cs_url, client_id, api_secret, max_retries=10, user_agent=None
    ):
        super(DciSignatureContext, self).__init__(
            dci_cs_url.rstrip("/"), max_retries, user_agent
        )
        self.session.auth = DciSignatureAuth(client_id, api_secret)


def build_signature_context(
    dci_cs_url=None,
    dci_client_id=None,
    dci_api_secret=None,
    user_agent=None,
    max_retries=10,
):
    dci_cs_url = dci_cs_url or os.environ.get("DCI_CS_URL", "")
    dci_client_id = dci_client_id or os.environ.get("DCI_CLIENT_ID", "")
    dci_api_secret = dci_api_secret or os.environ.get("DCI_API_SECRET", "")

    if not dci_cs_url or not dci_client_id or not dci_api_secret:
        msg = (
            "Environment variables required: DCI_CS_URL, "
            "DCI_CLIENT_ID, DCI_API_SECRET"
        )
        raise Exception(msg)
    return DciSignatureContext(
        dci_cs_url,
        dci_client_id,
        dci_api_secret,
        user_agent=user_agent,
        max_retries=max_retries,
    )


class JWTBearerAuth(AuthBase):
    """JWT Bearer authentication for DCI API with automatic token refresh"""

    def __init__(self, dci_cs_url, token_storage):
        self.dci_cs_url = dci_cs_url
        self.token_storage = token_storage

    def _refresh_access_token(self):
        """Refresh the access token using the refresh token"""
        refresh_token = self.token_storage.get_refresh_token()
        if not refresh_token:
            raise Exception("No valid refresh token available. Please login again.")

        url = "%s/%s/auth/refresh" % (self.dci_cs_url, DciContext.API_VERSION)
        headers = {
            "Authorization": "JWTBearer %s" % refresh_token,
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            tokens = response.json()

            # Save new tokens
            self.token_storage.save_tokens(
                tokens["access_token"],
                tokens["refresh_token"]
            )

            return tokens["access_token"]
        except requests.exceptions.RequestException as e:
            raise Exception("Failed to refresh token: %s" % str(e))

    def __call__(self, r):
        # Check if access token is expired and refresh if needed
        access_token = self.token_storage.get_valid_access_token()

        if not access_token:
            # Try to refresh
            access_token = self._refresh_access_token()

        if not access_token:
            raise Exception("No valid access token available. Please login again.")

        r.headers["Authorization"] = "JWTBearer %s" % access_token
        return r


class JWTContext(DciContextBase):
    """DCI Context using JWT Bearer authentication with automatic token refresh"""

    def __init__(self, dci_cs_url, token_storage=None, max_retries=10, user_agent=None):
        super(JWTContext, self).__init__(
            dci_cs_url.rstrip("/"), max_retries, user_agent
        )
        if token_storage is None:
            token_storage = TokenStorage()
        self.token_storage = token_storage
        self.session.auth = JWTBearerAuth(dci_cs_url.rstrip("/"), token_storage)

    def login(self, email, password):
        """
        Login with credentials and store JWT tokens.

        Args:
            email: User email address
            password: User password

        Raises:
            requests.exceptions.HTTPError: If login fails
        """
        login_url = "%s/auth/login" % self.dci_cs_api

        # Temporarily remove auth to avoid trying to use non-existent tokens
        old_auth = self.session.auth
        self.session.auth = None

        try:
            response = self.session.post(
                login_url,
                json={"email": email, "password": password},
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

            tokens = response.json()
            self.token_storage.save_tokens(tokens["access_token"], tokens["refresh_token"])
        finally:
            # Restore auth
            self.session.auth = old_auth


class SsoContext(DciContextBase):
    def __init__(self, dci_cs_url, token, max_retries=10, user_agent=None):
        super(SsoContext, self).__init__(
            dci_cs_url.rstrip("/"), max_retries, user_agent
        )
        self.session.headers["Authorization"] = "Bearer %s" % token


def build_jwt_context(dci_cs_url=None, token_storage=None, max_retries=10, user_agent=None):
    """
    Build a JWT context using stored tokens.

    Args:
        dci_cs_url: DCI Control Server URL
        token_storage: TokenStorage instance (optional)
        max_retries: Maximum number of retries
        user_agent: Custom user agent string

    Returns:
        JWTContext: Context configured with JWT authentication

    Raises:
        Exception: If no tokens are available
    """
    dci_cs_url = dci_cs_url or os.environ.get("DCI_CS_URL", "")
    if not dci_cs_url:
        raise Exception("DCI_CS_URL is required")

    if token_storage is None:
        token_storage = TokenStorage()

    # Check if tokens exist
    if not token_storage.load_tokens():
        raise Exception(
            "No JWT tokens found. Please run 'dcictl login' first."
        )

    return JWTContext(dci_cs_url, token_storage, max_retries, user_agent)


def build_sso_context(
    dci_cs_url,
    sso_url,
    username,
    password,
    token,
    max_retries=10,
    user_agent=None,
    refresh=False,
):
    def _get_token_from_file(token_path):
        if os.path.exists(token_path):
            with open(token_path, "r") as f:
                return f.read()
        return None

    def _write_token_to_file(token_path, token):
        cache_folder = os.path.dirname(token_path)
        if not os.path.exists(cache_folder):
            os.makedirs(cache_folder)

        with open(token_path, "w") as f:
            f.write(token)

    def _get_token_from_server(sso_url, username, password):
        url = "%s/auth/realms/redhat-external/protocol/openid-connect/token" % sso_url
        data = {
            "client_id": "dci",
            "grant_type": "password",
            "username": username,
            "password": password,
        }
        result = requests.Session().post(url, data=data)
        return result.json()["access_token"]

    token_path = os.path.join(os.environ["HOME"], ".cache", "dci_token")
    token = token or _get_token_from_file(token_path)

    if not token or refresh:
        sso_url = sso_url or os.environ.get("SSO_URL", "").rstrip("/")
        username = username or os.environ.get("SSO_USERNAME", "")
        password = password or os.environ.get("SSO_PASSWORD", "")
        if not sso_url or not username or not password:
            msg = (
                "Environment variables required to build token: SSO_URL, "
                "SSO_USERNAME, SSO_PASSWORD or use SSO_TOKEN."
            )
            raise Exception(msg)
        token = _get_token_from_server(sso_url, username, password)
        _write_token_to_file(token_path, token)

    dci_cs_url = dci_cs_url or os.environ.get("DCI_CS_URL", "")
    return SsoContext(dci_cs_url, token, max_retries, user_agent)
