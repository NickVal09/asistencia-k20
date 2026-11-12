import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool, text

from alembic import context

# Agregar backend al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.models import Base

# Validación de seguridad obligatoria:
if settings.MYSQL_DB != "asistencia_k20":
    raise RuntimeError(
        f"ALERTA DE SEGURIDAD: La base de datos configurada es '{settings.MYSQL_DB}', "
        f"pero las migraciones SOLO pueden ejecutarse sobre 'asistencia_k20'."
    )

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Configurar URL de conexión dinámicamente desde settings
config.set_main_option("sqlalchemy.url", settings.SQLALCHEMY_DATABASE_URI)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.SQLALCHEMY_DATABASE_URI

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    # Se usa begin() (no connect()) para confirmar la escritura en
    # alembic_version. MySQL no tiene DDL transaccional, por lo que con
    # connect() la fila de versión se perdía al cerrar la conexión.
    with connectable.begin() as connection:
        # Doble verificación directa en el motor de conexión
        db_name = connection.execute(text("SELECT DATABASE()")).scalar()
        if db_name and db_name != "asistencia_k20":
            raise RuntimeError(f"Conexión activa apunta a '{db_name}'. Abortando para proteger otras bases de datos.")

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
