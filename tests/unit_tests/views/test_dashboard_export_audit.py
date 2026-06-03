# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from unittest.mock import MagicMock, patch

from flask import Flask

from superset.views.dashboard.views import DashboardModelView


@patch("superset.views.dashboard.views.url_for")
@patch("superset.views.dashboard.views.redirect")
@patch("superset.views.dashboard.views.get_user_id", return_value=42)
@patch("superset.views.dashboard.views.event_logger")
def test_mulexport_logs_dashboard_export_event(
    mock_event_logger: MagicMock,
    mock_get_user_id: MagicMock,
    mock_redirect: MagicMock,
    mock_url_for: MagicMock,
) -> None:
    """mulexport() logs a DashboardExport audit event per DORA Art.9."""
    app = Flask(__name__)
    with app.test_request_context(
        "/", headers={"Referer": "http://localhost/dashboard/list/"}
    ):
        app.config["SESSION_COOKIE_NAME"] = "session"

        view = DashboardModelView.__new__(DashboardModelView)

        item1 = MagicMock()
        item1.id = 1
        item2 = MagicMock()
        item2.id = 2

        view.mulexport([item1, item2])

        mock_event_logger.log.assert_called_once_with(
            user_id=42,
            action="DashboardExport",
            dashboard_id=None,
            duration_ms=None,
            slice_id=None,
            referrer="http://localhost/dashboard/list/",
            curated_payload=None,
            curated_form_data=None,
            records=[
                {
                    "dashboard_ids": [1, 2],
                    "dashboard_count": 2,
                    "session_id": "",
                }
            ],
        )


@patch("superset.views.dashboard.views.url_for")
@patch("superset.views.dashboard.views.redirect")
@patch("superset.views.dashboard.views.get_user_id", return_value=7)
@patch("superset.views.dashboard.views.event_logger")
def test_mulexport_wraps_single_item_in_list(
    mock_event_logger: MagicMock,
    mock_get_user_id: MagicMock,
    mock_redirect: MagicMock,
    mock_url_for: MagicMock,
) -> None:
    """mulexport() handles a single item (not a list) and still logs."""
    app = Flask(__name__)
    with app.test_request_context("/"):
        view = DashboardModelView.__new__(DashboardModelView)

        item = MagicMock()
        item.id = 5

        view.mulexport(item)

        mock_event_logger.log.assert_called_once_with(
            user_id=7,
            action="DashboardExport",
            dashboard_id=None,
            duration_ms=None,
            slice_id=None,
            referrer=None,
            curated_payload=None,
            curated_form_data=None,
            records=[
                {
                    "dashboard_ids": [5],
                    "dashboard_count": 1,
                    "session_id": "",
                }
            ],
        )
