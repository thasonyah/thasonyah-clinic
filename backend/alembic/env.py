from sqlalchemy import create_engine, pool

from alembic import context
from app.config import get_settings
from app.database import Base
from app.models import (  # noqa: F401
    audit,
    billing,
    catalog,
    identity,
    pharmacy,
    records,  # noqa: F401
    scheduling,
)

config = context.config
target_metadata = Base.metadata
url = get_settings().sqlalchemy_url

if context.is_offline_mode():
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = create_engine(url, poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
