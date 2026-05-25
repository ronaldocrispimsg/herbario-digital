from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum


# ─── Enums ────────────────────────────────────────────────────────────────────

class PerfilUsuario(str, Enum):
    administrador = "administrador"
    curador = "curador"
    leitor = "leitor"


class StatusEspecime(str, Enum):
    ativo = "ativo"
    emprestado = "emprestado"
    em_processamento = "em_processamento"
    descartado = "descartado"


class TipoColeta(str, Enum):
    campo = "campo"
    doacao = "doacao"
    intercambio = "intercambio"
    compra = "compra"


# ─── Usuario ──────────────────────────────────────────────────────────────────

class UsuarioBase(BaseModel):
    nome: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    perfil: PerfilUsuario = PerfilUsuario.leitor


class UsuarioCreate(UsuarioBase):
    senha: str = Field(..., min_length=8, description="Mínimo 8 caracteres")

    @field_validator("senha")
    @classmethod
    def validar_senha(cls, value: str) -> str:
        return validar_senha_usuario(value)


class UsuarioUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=2, max_length=150)
    email: Optional[EmailStr] = None
    perfil: Optional[PerfilUsuario] = None
    ativo: Optional[bool] = None
    senha: Optional[str] = Field(None, min_length=8)

    @field_validator("senha")
    @classmethod
    def validar_senha(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return validar_senha_usuario(value)


class UsuarioSelfUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=2, max_length=150)
    email: Optional[EmailStr] = None
    senha: Optional[str] = Field(None, min_length=8)

    @field_validator("senha")
    @classmethod
    def validar_senha(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return validar_senha_usuario(value)


def validar_senha_usuario(value: str) -> str:
    if value.isdigit():
        raise ValueError("A senha não pode conter apenas números")
    if not any(ch.isalpha() for ch in value):
        raise ValueError("A senha deve conter pelo menos uma letra")
    if not any(ch.isdigit() for ch in value):
        raise ValueError("A senha deve conter pelo menos um número")
    return value


class UsuarioOut(UsuarioBase):
    id: int
    email: str
    ativo: bool
    criado_em: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut


class ExportDwcaRequest(BaseModel):
    ids: Optional[List[int]] = None


# ─── Taxonomia ────────────────────────────────────────────────────────────────

class TaxonomiaBase(BaseModel):
    reino: Optional[str] = None
    filo: Optional[str] = None
    classe: Optional[str] = None
    ordem: Optional[str] = None
    familia: Optional[str] = None
    genero: Optional[str] = None
    epiteto_especifico: Optional[str] = None
    nome_cientifico: str = Field(..., min_length=3)
    autor_descricao: Optional[str] = None
    ano_descricao: Optional[int] = Field(None, ge=1700, le=2100)
    nome_comum: Optional[str] = None
    sinonimos: Optional[List[str]] = []
    notas_taxonomicas: Optional[str] = None


class TaxonomiaCreate(TaxonomiaBase):
    pass


class TaxonomiaUpdate(BaseModel):
    reino: Optional[str] = None
    filo: Optional[str] = None
    classe: Optional[str] = None
    ordem: Optional[str] = None
    familia: Optional[str] = None
    genero: Optional[str] = None
    epiteto_especifico: Optional[str] = None
    nome_cientifico: Optional[str] = None
    autor_descricao: Optional[str] = None
    ano_descricao: Optional[int] = Field(None, ge=1700, le=2100)
    nome_comum: Optional[str] = None
    sinonimos: Optional[List[str]] = None
    notas_taxonomicas: Optional[str] = None


class TaxonomiaOut(TaxonomiaBase):
    id: int
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True


# ─── Localidade ───────────────────────────────────────────────────────────────

class LocalidadeBase(BaseModel):
    pais: str = "Brasil"
    estado: Optional[str] = None
    municipio: Optional[str] = None
    localidade: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    altitude_m: Optional[float] = None
    datum_geodesico: str = "WGS84"
    precisao_coordenadas_m: Optional[float] = None
    metodo_geolocalizacao: Optional[str] = None
    bioma: Optional[str] = None


class LocalidadeCreate(LocalidadeBase):
    pass


class LocalidadeUpdate(BaseModel):
    pais: Optional[str] = None
    estado: Optional[str] = None
    municipio: Optional[str] = None
    localidade: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    altitude_m: Optional[float] = None
    datum_geodesico: Optional[str] = None
    precisao_coordenadas_m: Optional[float] = None
    metodo_geolocalizacao: Optional[str] = None
    bioma: Optional[str] = None


class LocalidadeOut(LocalidadeBase):
    id: int
    criado_em: datetime

    class Config:
        from_attributes = True


# ─── Imagem ───────────────────────────────────────────────────────────────────

class ImagemOut(BaseModel):
    id: int
    especime_id: int
    nome_arquivo: str
    url_relativa: Optional[str]
    tipo_mime: Optional[str]
    tamanho_bytes: Optional[int]
    largura_px: Optional[int]
    altura_px: Optional[int]
    descricao: Optional[str]
    is_principal: bool
    criado_em: datetime

    class Config:
        from_attributes = True


# ─── Espécime ─────────────────────────────────────────────────────────────────

class EspecimeBase(BaseModel):
    codigo_catalogo: str = Field(..., min_length=1, max_length=50)
    taxonomia_id: int
    data_coleta: Optional[datetime] = None
    data_coleta_fim: Optional[datetime] = None
    tipo_coleta: TipoColeta = TipoColeta.campo
    coletor_principal: Optional[str] = None
    coletores_adicionais: Optional[List[str]] = []
    numero_campo: Optional[str] = None
    localidade_id: Optional[int] = None
    sexo: Optional[str] = None
    estagio_vida: Optional[str] = None
    condicao: Optional[str] = None
    numero_individuos: int = 1
    descricao_morfologica: Optional[str] = None
    observacoes: Optional[str] = None
    habitat: Optional[str] = None
    identificado_por: Optional[str] = None
    data_identificacao: Optional[datetime] = None
    metodo_identificacao: Optional[str] = None
    nivel_confianca_id: Optional[str] = None
    voucher_genbank: Optional[str] = None
    status: StatusEspecime = StatusEspecime.ativo
    localizacao_fisica: Optional[str] = None
    meio_preservacao: Optional[str] = None
    dwc_dataset_id: Optional[str] = None
    referencias_bibliograficas: Optional[List[str]] = []
    direitos: str = "CC BY 4.0"
    licenca: Optional[str] = None


class EspecimeCreate(EspecimeBase):
    pass


class EspecimeUpdate(BaseModel):
    codigo_catalogo: Optional[str] = None
    taxonomia_id: Optional[int] = None
    data_coleta: Optional[datetime] = None
    data_coleta_fim: Optional[datetime] = None
    tipo_coleta: Optional[TipoColeta] = None
    coletor_principal: Optional[str] = None
    coletores_adicionais: Optional[List[str]] = None
    numero_campo: Optional[str] = None
    localidade_id: Optional[int] = None
    sexo: Optional[str] = None
    estagio_vida: Optional[str] = None
    condicao: Optional[str] = None
    numero_individuos: Optional[int] = None
    descricao_morfologica: Optional[str] = None
    observacoes: Optional[str] = None
    habitat: Optional[str] = None
    identificado_por: Optional[str] = None
    data_identificacao: Optional[datetime] = None
    metodo_identificacao: Optional[str] = None
    nivel_confianca_id: Optional[str] = None
    voucher_genbank: Optional[str] = None
    status: Optional[StatusEspecime] = None
    localizacao_fisica: Optional[str] = None
    meio_preservacao: Optional[str] = None
    dwc_dataset_id: Optional[str] = None
    referencias_bibliograficas: Optional[List[str]] = None
    direitos: Optional[str] = None
    licenca: Optional[str] = None


class EspecimeOut(EspecimeBase):
    id: int
    codigo_barras: Optional[str]
    dwc_record_id: Optional[str]
    data_entrada_colecao: datetime
    cadastrado_por_id: Optional[int]
    criado_em: datetime
    atualizado_em: datetime
    taxonomia: Optional[TaxonomiaOut] = None
    localidade: Optional[LocalidadeOut] = None
    imagens: Optional[List[ImagemOut]] = []

    class Config:
        from_attributes = True


# ─── Empréstimo ───────────────────────────────────────────────────────────────

class EmprestimoBase(BaseModel):
    especime_id: int
    instituicao_destino: str = Field(..., min_length=2)
    pesquisador_responsavel: str = Field(..., min_length=2)
    finalidade: Optional[str] = None
    data_saida: datetime
    data_prevista_retorno: Optional[datetime] = None
    observacoes: Optional[str] = None


class EmprestimoCreate(EmprestimoBase):
    pass


class EmprestimoUpdate(BaseModel):
    data_prevista_retorno: Optional[datetime] = None
    data_retorno: Optional[datetime] = None
    observacoes: Optional[str] = None
    ativo: Optional[bool] = None


class EmprestimoOut(EmprestimoBase):
    id: int
    responsavel_id: int
    data_retorno: Optional[datetime]
    ativo: bool
    criado_em: datetime
    especime: Optional[EspecimeOut] = None

    class Config:
        from_attributes = True


# ─── Busca ────────────────────────────────────────────────────────────────────

class BuscaEspecime(BaseModel):
    nome_cientifico: Optional[str] = None
    familia: Optional[str] = None
    genero: Optional[str] = None
    estado: Optional[str] = None
    municipio: Optional[str] = None
    bioma: Optional[str] = None
    coletor: Optional[str] = None
    status: Optional[StatusEspecime] = None
    data_coleta_inicio: Optional[datetime] = None
    data_coleta_fim: Optional[datetime] = None
    lat_min: Optional[float] = Field(None, ge=-90, le=90)
    lat_max: Optional[float] = Field(None, ge=-90, le=90)
    lon_min: Optional[float] = Field(None, ge=-180, le=180)
    lon_max: Optional[float] = Field(None, ge=-180, le=180)
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    items: List[Any]
