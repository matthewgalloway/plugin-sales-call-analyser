import dataiku

from flask import request, Request
import json

from nbm_analysis.utils.logging_utils import get_logger

from typing import List, Dict, Any

logger = get_logger(__name__)


class DKUProjectAuthorization:
    def __init__(self) -> None:

        self._dataiku_client = dataiku.api_client()
        self._project_handle = self._dataiku_client.get_default_project()

    def get_admin_groups(self) -> List[str | None]:

        group_permissions = self._project_handle.get_permissions().get("permissions")
        return [d["group"] for d in group_permissions if d["admin"] is True]

    def get_auth_username_from_browser_headers(self, request: Request) -> str:
        request_headers = dict(request.headers)
        auth_info_browser = self._dataiku_client.get_auth_info_from_browser_headers(
            request_headers
        )
        auth_username: str = auth_info_browser.get("associatedDSSUser").replace(
            "@dataiku.com", ""
        )

        logger.debug(f"DSS-authenticated login is: {auth_username}")

        return auth_username

    def get_auth_user_group_from_browser_headers(self, request: Request) -> List[str]:
        request_headers = dict(request.headers)
        auth_info_browser = self._dataiku_client.get_auth_info_from_browser_headers(
            request_headers
        )

        auth_user_groups: List[str] = auth_info_browser.get("groups")

        logger.debug(f"DSS-authenticated user groups are: {auth_user_groups}")

        return auth_user_groups

    def is_user_admin(self, request: Request) -> bool:

        auth_user_groups = self.get_auth_user_group_from_browser_headers(request)
        admin_groups = self.get_admin_groups()

        return any([True for group in auth_user_groups if group in admin_groups])

    def get_auth_user_from_browser_headers(
        self, request: Request
    ) -> Dict[str, str | bool]:

        auth_username = self.get_auth_username_from_browser_headers(request)
        is_admin = self.is_user_admin(request)

        return {"username": auth_username, "is_admin": is_admin}

