import json
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
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

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        password_str = f":{self.MYSQL_PASSWORD}" if self.MYSQL_PASSWORD else ""
        return (
            f"mysql+pymysql://{self.MYSQL_USER}{password_str}@"
            f"{self.MYSQL_SERVER}:{self.MYSQL_PORT}/{self.MYSQL_DB}?charset=utf8mb4"
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()

