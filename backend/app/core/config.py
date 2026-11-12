import json
import re
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Sistema de Control de Asistencia K20"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "k20-dev-secret-key-zkteco-attendance-management-2026"
    ENVIRONMENT: str = "development"

    # Database
    MYSQL_SERVER: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DB: str = "asistencia_k20"

    # Biometric Device ZKTeco K20
    ZK_DEVICE_IP: str = "192.168.10.69"
    ZK_DEVICE_PORT: int = 4370
    ZK_DEVICE_PLATFORM: str = "ZLM60_TFT"
    ZK_DEVICE_NAME: str = "ZKTeco K20"

    # Paths
    CSV_DATA_PATH: str = "../datos/registros_k20.csv"
    EXPORTS_DIR: str = "./exports"

    # Security
    API_ACCESS_TOKEN: str = "k20-access-token-dev"
    ADMIN_USER: str = "admin"
    ADMIN_PASSWORD: str = ""          # solo desarrollo; en produccion usar ADMIN_PASSWORD_HASH
    ADMIN_PASSWORD_HASH: str = ""     # formato: pbkdf2_sha256$iteraciones$salt$hash
    TOKEN_EXPIRACION_MINUTOS: int = 480
    LOGIN_MAX_INTENTOS: int = 5
    LOGIN_BLOQUEO_MINUTOS: int = 5

    # Sincronizacion biometrica (Fase 2)
    SYNC_AUTOMATICA_ENABLED: bool = False
    SYNC_INTERVALO_MINUTOS: int = 10
    ZK_TIMEOUT_SEGUNDOS: int = 10
    ZK_REINTENTOS: int = 2
    SYNC_EJECUCION_COLGADA_MINUTOS: int = 30

    # Consulta de DNI (RENIEC) via AQPFACT
    AQPFACT_API_URL: str = "https://apis.aqpfact.pe/api"
    AQPFACT_API_TOKEN: str = ""
    AQPFACT_TIMEOUT_SEGUNDOS: int = 15

    ALLOWED_HOSTS: List[str] = ["127.0.0.1", "localhost"]
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str) and v.startswith("["):
            return json.loads(v)
        return v

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def assemble_allowed_hosts(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str) and v.startswith("["):
            return json.loads(v)
        return v

    # --- Limpieza tolerante de las variables de MySQL -----------------------
    # En Dokploy es habitual pegar el host con esquema, credenciales, ruta o
    # incluso con el puerto pegado ("192.168.10.62:3307"). Eso rompia la URL de
    # SQLAlchemy y el contenedor moria al importar. Aqui lo normalizamos.

    @field_validator("MYSQL_SERVER", mode="before")
    @classmethod
    def limpiar_mysql_server(cls, v: Union[str, None]) -> str:
        if v is None:
            return "127.0.0.1"
        valor = str(v).strip().strip('"').strip("'")
        if not valor:
            return "127.0.0.1"
        for prefijo in ("mysql+pymysql://", "mysql://", "http://", "https://"):
            if valor.lower().startswith(prefijo):
                valor = valor[len(prefijo):]
        if "@" in valor:                      # usuario:clave@host
            valor = valor.rsplit("@", 1)[1]
        valor = valor.split("/")[0]           # quitar /nombre_bd
        return valor.strip() or "127.0.0.1"

    @field_validator("MYSQL_PORT", mode="before")
    @classmethod
    def limpiar_mysql_port(cls, v: Union[str, int, None]) -> int:
        if v is None or v == "":
            return 3306
        texto = str(v).strip()
        digitos = re.sub(r"[^0-9]", "", texto)
        if digitos:
            return int(digitos)
        return 3306

    @field_validator("MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DB", mode="before")
    @classmethod
    def limpiar_texto_mysql(cls, v: Union[str, None]) -> str:
        if v is None:
            return ""
        return str(v).strip().strip('"').strip("'")

    @model_validator(mode="after")
    def separar_host_y_puerto(self):
        """Si pegaron 'host:puerto' en MYSQL_SERVER, separa el puerto."""
        servidor = self.MYSQL_SERVER or ""
        if servidor.count(":") == 1:
            host, _, posible_puerto = servidor.rpartition(":")
            if posible_puerto.isdigit() and host:
                object.__setattr__(self, "MYSQL_SERVER", host)
                object.__setattr__(self, "MYSQL_PORT", int(posible_puerto))
        return self

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        from sqlalchemy.engine import URL

        # URL.create escapa automaticamente claves con @ : / % # etc.
        return URL.create(
            drivername="mysql+pymysql",
            username=self.MYSQL_USER or None,
            password=self.MYSQL_PASSWORD or None,
            host=self.MYSQL_SERVER or None,
            port=self.MYSQL_PORT or 3306,
            database=self.MYSQL_DB or None,
            query={"charset": "utf8mb4"},
        ).render_as_string(hide_password=False)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()

