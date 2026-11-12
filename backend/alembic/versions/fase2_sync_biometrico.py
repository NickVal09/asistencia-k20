"""fase2 sincronizacion biometrica

Agrega los campos de estado real de conexion del dispositivo y de auditoria
de las sincronizaciones con el biomertico K20 (Fase 2).

No elimina ni modifica datos existentes: solo agrega columnas nuevas.

Revision ID: fase2_sync_biometrico
Revises: 704595c7a33c
Create Date: 2026-11-11 20:00:00.000000+00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fase2_sync_biometrico'
down_revision: Union[str, None] = '704595c7a33c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _tiene_columna(tabla: str, columna: str) -> bool:
    """Verifica si una columna ya existe (permite re-ejecutar sin romper)."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return columna in {c["name"] for c in inspector.get_columns(tabla)}


def upgrade() -> None:
    # --- dispositivos: estado real de conexion ---
    if not _tiene_columna("dispositivos", "ultima_conexion_ok"):
        op.add_column("dispositivos", sa.Column("ultima_conexion_ok", sa.DateTime(), nullable=True))
    if not _tiene_columna("dispositivos", "ultimo_error"):
        op.add_column("dispositivos", sa.Column("ultimo_error", sa.String(length=255), nullable=True))
    if not _tiene_columna("dispositivos", "ultimo_error_el"):
        op.add_column("dispositivos", sa.Column("ultimo_error_el", sa.DateTime(), nullable=True))
    if not _tiene_columna("dispositivos", "ultimo_modo_conexion"):
        op.add_column("dispositivos", sa.Column("ultimo_modo_conexion", sa.String(length=20), nullable=True))

    # --- ejecuciones_sincronizacion: auditoria de la sincronizacion ---
    if not _tiene_columna("ejecuciones_sincronizacion", "modo"):
        op.add_column("ejecuciones_sincronizacion", sa.Column("modo", sa.String(length=20), nullable=True))
    if not _tiene_columna("ejecuciones_sincronizacion", "conexion_ok"):
        op.add_column("ejecuciones_sincronizacion", sa.Column("conexion_ok", sa.Boolean(), nullable=True))
    if not _tiene_columna("ejecuciones_sincronizacion", "duracion_segundos"):
        op.add_column("ejecuciones_sincronizacion", sa.Column("duracion_segundos", sa.Float(), nullable=True))
    if not _tiene_columna("ejecuciones_sincronizacion", "ultima_marcacion"):
        op.add_column("ejecuciones_sincronizacion", sa.Column("ultima_marcacion", sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Se eliminan solo las columnas agregadas en esta migracion.
    for columna in ("ultima_marcacion", "duracion_segundos", "conexion_ok", "modo"):
        if _tiene_columna("ejecuciones_sincronizacion", columna):
            op.drop_column("ejecuciones_sincronizacion", columna)

    for columna in ("ultimo_modo_conexion", "ultimo_error_el", "ultimo_error", "ultima_conexion_ok"):
        if _tiene_columna("dispositivos", columna):
            op.drop_column("dispositivos", columna)
