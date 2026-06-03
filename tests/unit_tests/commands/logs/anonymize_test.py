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

from superset.commands.logs.anonymize import (
    _scrub_pii,
    ANONYMIZED_VALUE,
    LogAnonymizeCommand,
    PII_FIELDS,
)
from superset.utils import json

# ------------------------------------------------------------------
# _scrub_pii unit tests
# ------------------------------------------------------------------


def test_scrub_pii_replaces_known_fields() -> None:
    payload = json.dumps({"username": "alice", "user_id": 1})
    result = json.loads(_scrub_pii(payload))
    assert result["username"] == ANONYMIZED_VALUE
    assert result["user_id"] == 1


def test_scrub_pii_replaces_all_pii_fields() -> None:
    payload = json.dumps(
        {
            "username": "alice",
            "email": "alice@example.com",
            "target_username": "bob",
            "first_name": "Alice",
            "last_name": "Smith",
            "other": "safe",
        }
    )
    result = json.loads(_scrub_pii(payload))
    for field in PII_FIELDS:
        assert result[field] == ANONYMIZED_VALUE
    assert result["other"] == "safe"


def test_scrub_pii_no_pii_returns_original() -> None:
    payload = json.dumps({"action": "login", "user_id": 5})
    assert _scrub_pii(payload) == payload


def test_scrub_pii_invalid_json_returns_original() -> None:
    bad = "not-json"
    assert _scrub_pii(bad) == bad


def test_scrub_pii_non_dict_json_returns_original() -> None:
    arr = json.dumps([1, 2, 3])
    assert _scrub_pii(arr) == arr


# ------------------------------------------------------------------
# LogAnonymizeCommand unit tests (mocked DB)
# ------------------------------------------------------------------


@patch("superset.commands.logs.anonymize.db")
def test_anonymize_command_nullifies_user_id_and_scrubs_pii(
    mock_db: MagicMock,
) -> None:
    """LogAnonymizeCommand sets user_id=None and scrubs PII in JSON payloads."""
    log_row = MagicMock()
    log_row.id = 10
    log_row.user_id = 42
    log_row.json = json.dumps({"username": "alice", "user_id": 42})

    # First query: select IDs
    mock_scalars_ids = MagicMock()
    mock_scalars_ids.all.return_value = [10]

    # Second query: select Log objects
    mock_scalars_rows = MagicMock()
    mock_scalars_rows.all.return_value = [log_row]

    mock_db.session.execute.side_effect = [
        MagicMock(scalars=MagicMock(return_value=mock_scalars_ids)),
        MagicMock(scalars=MagicMock(return_value=mock_scalars_rows)),
    ]

    result = LogAnonymizeCommand(42).run()

    assert result == 1
    assert log_row.user_id is None
    scrubbed = json.loads(log_row.json)
    assert scrubbed["username"] == ANONYMIZED_VALUE
    assert scrubbed["user_id"] == 42
    mock_db.session.commit.assert_called_once()


@patch("superset.commands.logs.anonymize.db")
def test_anonymize_command_returns_zero_when_no_rows(mock_db: MagicMock) -> None:
    """LogAnonymizeCommand returns 0 when the user has no log rows."""
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_db.session.execute.return_value = MagicMock(
        scalars=MagicMock(return_value=mock_scalars)
    )

    result = LogAnonymizeCommand(999).run()
    assert result == 0
    mock_db.session.commit.assert_not_called()


@patch("superset.commands.logs.anonymize.db")
def test_anonymize_command_handles_null_json(mock_db: MagicMock) -> None:
    """LogAnonymizeCommand handles rows where json is None."""
    log_row = MagicMock()
    log_row.id = 5
    log_row.user_id = 7
    log_row.json = None

    mock_scalars_ids = MagicMock()
    mock_scalars_ids.all.return_value = [5]
    mock_scalars_rows = MagicMock()
    mock_scalars_rows.all.return_value = [log_row]

    mock_db.session.execute.side_effect = [
        MagicMock(scalars=MagicMock(return_value=mock_scalars_ids)),
        MagicMock(scalars=MagicMock(return_value=mock_scalars_rows)),
    ]

    result = LogAnonymizeCommand(7).run()
    assert result == 1
    assert log_row.user_id is None
    assert log_row.json is None
