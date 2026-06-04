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
"""DORA Art.9: Verify audit logging on dashboard export (mulexport)."""

from unittest.mock import MagicMock, patch


@patch("superset.views.dashboard.views.redirect")
@patch("superset.views.dashboard.views.url_for")
def test_mulexport_calls_audit_logger(
    mock_url_for: MagicMock,
    mock_redirect: MagicMock,
) -> None:
    """mulexport() must invoke add_extra_log_payload for DORA Art.9 compliance."""
    from superset.views.dashboard.views import DashboardModelView

    view = DashboardModelView.__new__(DashboardModelView)

    item = MagicMock()
    item.id = 1

    log_payload = MagicMock()
    # Call the unwrapped function to bypass the event_logger decorator
    DashboardModelView.mulexport.__wrapped__(
        view, [item], add_extra_log_payload=log_payload
    )

    log_payload.assert_called_once_with(
        action="dashboard_export",
        dashboard_ids=[1],
        dashboard_count=1,
    )


@patch("superset.views.dashboard.views.redirect")
@patch("superset.views.dashboard.views.url_for")
def test_mulexport_logs_multiple_dashboards(
    mock_url_for: MagicMock,
    mock_redirect: MagicMock,
) -> None:
    """mulexport() logs all dashboard IDs when exporting multiple dashboards."""
    from superset.views.dashboard.views import DashboardModelView

    view = DashboardModelView.__new__(DashboardModelView)

    items = [MagicMock(id=10), MagicMock(id=20), MagicMock(id=30)]

    log_payload = MagicMock()
    DashboardModelView.mulexport.__wrapped__(
        view, items, add_extra_log_payload=log_payload
    )

    log_payload.assert_called_once_with(
        action="dashboard_export",
        dashboard_ids=[10, 20, 30],
        dashboard_count=3,
    )


@patch("superset.views.dashboard.views.redirect")
@patch("superset.views.dashboard.views.url_for")
def test_mulexport_wraps_single_item_in_list(
    mock_url_for: MagicMock,
    mock_redirect: MagicMock,
) -> None:
    """mulexport() normalises a single item into a list before logging."""
    from superset.views.dashboard.views import DashboardModelView

    view = DashboardModelView.__new__(DashboardModelView)

    item = MagicMock()
    item.id = 5

    log_payload = MagicMock()
    DashboardModelView.mulexport.__wrapped__(
        view, item, add_extra_log_payload=log_payload
    )

    log_payload.assert_called_once_with(
        action="dashboard_export",
        dashboard_ids=[5],
        dashboard_count=1,
    )


def test_mulexport_has_event_logger_decorator() -> None:
    """mulexport() must be wrapped by @event_logger.log_this_with_extra_payload."""
    from superset.views.dashboard.views import DashboardModelView

    assert hasattr(DashboardModelView.mulexport, "__wrapped__"), (
        "mulexport is not decorated with @event_logger.log_this_with_extra_payload"
    )
