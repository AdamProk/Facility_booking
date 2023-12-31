"""Initial

Revision ID: 23d5b2416f07
Revises: 
Create Date: 2023-12-30 19:37:27.680997

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '23d5b2416f07'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('cities',
    sa.Column('id_city', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id_city'),
    sa.UniqueConstraint('name')
    )
    op.create_table('facility_types',
    sa.Column('id_facility_type', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id_facility_type'),
    sa.UniqueConstraint('name')
    )
    op.create_table('reservation_statuses',
    sa.Column('id_reservation_status', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id_reservation_status'),
    sa.UniqueConstraint('status')
    )
    op.create_table('states',
    sa.Column('id_state', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id_state'),
    sa.UniqueConstraint('name')
    )
    op.create_table('user_roles',
    sa.Column('id_user_role', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id_user_role'),
    sa.UniqueConstraint('name')
    )
    op.create_table('users',
    sa.Column('id_user', sa.Integer(), nullable=False),
    sa.Column('user_role_id', sa.Integer(), nullable=True),
    sa.Column('email', sa.String(), nullable=True),
    sa.Column('password', sa.String(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('lastname', sa.String(), nullable=True),
    sa.Column('phone_number', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['user_role_id'], ['user_roles.id_user_role'], ),
    sa.PrimaryKeyConstraint('id_user'),
    sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_id_user'), 'users', ['id_user'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_users_id_user'), table_name='users')
    op.drop_table('users')
    op.drop_table('user_roles')
    op.drop_table('states')
    op.drop_table('reservation_statuses')
    op.drop_table('facility_types')
    op.drop_table('cities')
    # ### end Alembic commands ###