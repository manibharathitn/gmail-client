"""create email table

Revision ID: 27ecb06f3df6
Revises: 
Create Date: 2024-03-23 21:55:17.185219

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '27ecb06f3df6'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'email',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('subject', sa.String(255), nullable=False),
        sa.Column('sender', sa.String(255), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('recipient', sa.String(255), nullable=False),
        sa.Column('cc', sa.String(255)),
        sa.Column('date_received', sa.DateTime, nullable=False),
        sa.Column('synced_at', sa.DateTime, nullable=False),
    )


def downgrade():
    op.drop_table('email')