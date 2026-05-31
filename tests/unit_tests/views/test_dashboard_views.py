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
"""Tests for DORA Art.9 audit logging on dashboard views."""

from superset.views.dashboard.views import DashboardModelView


def test_dashboard_list_has_event_logger_decorator() -> None:
    """DashboardModelView.list() must be decorated with @event_logger.log_this
    to satisfy DORA Art.9 ICT access event logging requirements."""
    list_method = DashboardModelView.list
    # event_logger.log_this uses functools.wraps, so __wrapped__ is set
    assert hasattr(list_method, "__wrapped__"), (
        "DashboardModelView.list must be decorated with @event_logger.log_this "
        "for DORA Art.9 compliance (ICT access event logging)"
    )
