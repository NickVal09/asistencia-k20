from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    usuario: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: str
    expira_en_minutos: int


class UsuarioInfo(BaseModel):
    usuario: str
    rol: str
    autenticado: bool = True
