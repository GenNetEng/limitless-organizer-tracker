"""add_event_log_table

Revision ID: b7e3a1f2c456
Revises: 59209420e443
Create Date: 2026-06-22 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7e3a1f2c456"
down_revision: Union[str, None] = "59209420e443"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    if is_postgres:
        op.execute(
            """
            CREATE TABLE event_log (
                id SERIAL,
                "timestamp" TIMESTAMPTZ NOT NULL,
                event_type VARCHAR NOT NULL,
                severity VARCHAR NOT NULL,
                source VARCHAR NOT NULL,
                message TEXT NOT NULL,
                details TEXT,
                correlation_id VARCHAR,
                PRIMARY KEY (id, "timestamp")
            ) PARTITION BY RANGE ("timestamp")
            """
        )
        op.execute(
            """
            CREATE INDEX ix_event_log_timestamp ON event_log ("timestamp")
            """
        )
        op.execute(
            """
            CREATE INDEX ix_event_log_event_type ON event_log (event_type)
            """
        )
        # Create initial monthly partitions (current + next 3 months)
        op.execute(
            """
            CREATE TABLE event_log_y2026m06 PARTITION OF event_log
                FOR VALUES FROM ('2026-06-01') TO ('2026-07-01')
            """
        )
        op.execute(
            """
            CREATE TABLE event_log_y2026m07 PARTITION OF event_log
                FOR VALUES FROM ('2026-07-01') TO ('2026-08-01')
            """
        )
        op.execute(
            """
            CREATE TABLE event_log_y2026m08 PARTITION OF event_log
                FOR VALUES FROM ('2026-08-01') TO ('2026-09-01')
            """
        )
        op.execute(
            """
            CREATE TABLE event_log_y2026m09 PARTITION OF event_log
                FOR VALUES FROM ('2026-09-01') TO ('2026-10-01')
            """
        )
    else:
        op.create_table(
            "event_log",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
            sa.Column("event_type", sa.String(), nullable=False),
            sa.Column("severity", sa.String(), nullable=False),
            sa.Column("source", sa.String(), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("details", sa.Text(), nullable=True),
            sa.Column("correlation_id", sa.String(), nullable=True),
        )
        op.create_index("ix_event_log_timestamp", "event_log", ["timestamp"])
        op.create_index("ix_event_log_event_type", "event_log", ["event_type"])


def downgrade() -> None:
    op.drop_index("ix_event_log_event_type", table_name="event_log")
    op.drop_index("ix_event_log_timestamp", table_name="event_log")
    op.drop_table("event_log")
