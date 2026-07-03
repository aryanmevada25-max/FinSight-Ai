"""Create the user authentication schema.

Revision ID: d3dae688dbb4
Revises: 
Create Date: 2026-07-01 19:35:23.595563

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd3dae688dbb4'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    if "users" not in inspector.get_table_names():
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("email", sa.String(length=120), nullable=False),
            sa.Column("password", sa.String(length=255), nullable=False),
            sa.Column(
                "currency",
                sa.String(length=3),
                server_default="USD",
                nullable=False,
            ),
            sa.Column(
                "monthly_budget",
                sa.Numeric(precision=12, scale=2),
                server_default="0.00",
                nullable=False,
            ),
            sa.Column(
                "created_at",
                sa.DateTime(),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_users_email", "users", ["email"], unique=True)
        return

    existing_columns = {
        column["name"] for column in inspector.get_columns("users")
    }
    existing_indexes = {
        index["name"] for index in inspector.get_indexes("users")
    }
    with op.batch_alter_table("users", recreate="always") as batch_op:
        if "currency" not in existing_columns:
            batch_op.add_column(
                sa.Column(
                    "currency",
                    sa.String(length=3),
                    server_default="USD",
                    nullable=False,
                )
            )
        if "monthly_budget" not in existing_columns:
            batch_op.add_column(
                sa.Column(
                    "monthly_budget",
                    sa.Numeric(precision=12, scale=2),
                    server_default="0.00",
                    nullable=False,
                )
            )
        if "created_at" not in existing_columns:
            batch_op.add_column(
                sa.Column(
                    "created_at",
                    sa.DateTime(),
                    server_default=sa.text("(CURRENT_TIMESTAMP)"),
                    nullable=False,
                )
            )
        if "updated_at" not in existing_columns:
            batch_op.add_column(
                sa.Column(
                    "updated_at",
                    sa.DateTime(),
                    server_default=sa.text("(CURRENT_TIMESTAMP)"),
                    nullable=False,
                )
            )
        if "ix_users_email" not in existing_indexes:
            batch_op.create_index("ix_users_email", ["email"], unique=True)


def downgrade():
    op.drop_table("users")
