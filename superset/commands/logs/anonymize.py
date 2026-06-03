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
import logging

import sqlalchemy as sa

from superset import db
from superset.commands.base import BaseCommand
from superset.models.core import Log
from superset.utils import json

logger = logging.getLogger(__name__)

# Fields in JSON audit payloads that contain PII and must be scrubbed.
PII_FIELDS = frozenset(
    {
        "username",
        "email",
        "target_username",
        "first_name",
        "last_name",
    }
)

ANONYMIZED_VALUE = "[REDACTED]"


class LogAnonymizeCommand(BaseCommand):
    """Anonymize audit-log rows that reference a specific user.

    Implements GDPR Article 17 (right to erasure) by:
    1. Setting ``user_id`` to ``NULL`` on every ``Log`` row belonging to the user.
    2. Scrubbing PII fields from the ``json`` payload of those rows.

    The command processes rows in batches to avoid excessive memory usage
    and commits after each batch so that partial progress is preserved if
    an error occurs.
    """

    def __init__(self, user_id: int) -> None:
        self.user_id = user_id

    def run(self) -> int:
        """Execute the anonymization and return the number of rows affected."""
        batch_size = 999
        total_updated = 0

        ids_to_update: list[int] = (
            db.session.execute(sa.select(Log.id).where(Log.user_id == self.user_id))
            .scalars()
            .all()
        )

        if not ids_to_update:
            logger.info(
                "No log rows found for user_id=%s; nothing to anonymize.",
                self.user_id,
            )
            return 0

        logger.info(
            "Anonymizing %s log row(s) for user_id=%s",
            len(ids_to_update),
            self.user_id,
        )

        for i in range(0, len(ids_to_update), batch_size):
            batch_ids = ids_to_update[i : i + batch_size]

            rows: list[Log] = (
                db.session.execute(sa.select(Log).where(Log.id.in_(batch_ids)))
                .scalars()
                .all()
            )

            for log_row in rows:
                log_row.user_id = None
                if log_row.json:
                    log_row.json = _scrub_pii(log_row.json)

            total_updated += len(rows)
            db.session.commit()  # pylint: disable=consider-using-transaction

        logger.info(
            "Anonymization complete: %s row(s) updated for former user_id=%s",
            total_updated,
            self.user_id,
        )
        return total_updated

    def validate(self) -> None:
        pass


def _scrub_pii(json_string: str) -> str:
    """Replace PII field values in a JSON audit payload with a redacted marker."""
    try:
        payload = json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return json_string

    if not isinstance(payload, dict):
        return json_string

    changed = False
    for field in PII_FIELDS:
        if field in payload:
            payload[field] = ANONYMIZED_VALUE
            changed = True

    return json.dumps(payload) if changed else json_string
