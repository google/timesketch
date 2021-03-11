"""Change the file size value of the data source to a larger int.

Revision ID: 41cae2c10cd7
Revises: 654121a84a33
Create Date: 2021-03-03 10:59:58.038715

"""
# pylint: skip-file

# revision identifiers, used by Alembic.
revision = '41cae2c10cd7'
down_revision = '654121a84a33'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('datasource', 'file_size', type_=sa.BigInteger)


def downgrade():
    op.alter_column('datasource', 'file_size', type_=sa.Integer)
