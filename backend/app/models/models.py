from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, Boolean,
    ForeignKey, Enum, Index, func
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
import enum

from app.db.session import Base


# ─── Enums ────────────────────────────────────────────────────────────────────

class PerfilUsuario(str, enum.Enum):
    administrador = "administrador"
    curador = "curador"
    leitor = "leitor"


class StatusEspecime(str, enum.Enum):
    ativo = "ativo"
    emprestado = "emprestado"
    em_processamento = "em_processamento"
    descartado = "descartado"


class TipoColeta(str, enum.Enum):
    campo = "campo"
    doacao = "doacao"
    intercambio = "intercambio"
    compra = "compra"


# ─── Modelos ──────────────────────────────────────────────────────────────────

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(150), nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    perfil = Column(Enum(PerfilUsuario), default=PerfilUsuario.leitor, nullable=False)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    especimes_cadastrados = relationship("Especime", back_populates="cadastrado_por_usuario")
    emprestimos = relationship("Emprestimo", back_populates="responsavel")


class Taxonomia(Base):
    __tablename__ = "taxonomias"

    id = Column(Integer, primary_key=True, index=True)
    reino = Column(String(100))
    filo = Column(String(100))
    classe = Column(String(100))
    ordem = Column(String(100))
    familia = Column(String(100), index=True)
    genero = Column(String(100), index=True)
    epiteto_especifico = Column(String(100))
    nome_cientifico = Column(String(250), nullable=False, index=True)
    autor_descricao = Column(String(200))
    ano_descricao = Column(Integer)
    nome_comum = Column(String(200))
    sinonimos = Column(JSONB, default=list)  # lista de sinônimos
    notas_taxonomicas = Column(Text)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    especimes = relationship("Especime", back_populates="taxonomia")

    __table_args__ = (
        Index("ix_taxonomia_nome_cientifico_trgm", "nome_cientifico"),
    )


class LocalidadeGeografica(Base):
    __tablename__ = "localidades_geograficas"

    id = Column(Integer, primary_key=True, index=True)
    pais = Column(String(100), nullable=False, default="Brasil")
    estado = Column(String(100))
    municipio = Column(String(150))
    localidade = Column(String(300))  # descrição textual detalhada
    latitude = Column(Float)
    longitude = Column(Float)
    altitude_m = Column(Float)
    datum_geodesico = Column(String(50), default="WGS84")
    precisao_coordenadas_m = Column(Float)
    metodo_geolocalizacao = Column(String(100))  # GPS, Google Maps, etc.
    bioma = Column(String(100))
    criado_em = Column(DateTime, default=datetime.utcnow)

    especimes = relationship("Especime", back_populates="localidade")


class Especime(Base):
    __tablename__ = "especimes"

    id = Column(Integer, primary_key=True, index=True)
    codigo_catalogo = Column(String(50), unique=True, nullable=False, index=True)
    codigo_barras = Column(String(100), unique=True, index=True)

    # Identificação taxonômica
    taxonomia_id = Column(Integer, ForeignKey("taxonomias.id"), nullable=False)
    taxonomia = relationship("Taxonomia", back_populates="especimes")

    # Dados de coleta
    data_coleta = Column(DateTime)
    data_coleta_fim = Column(DateTime)  # para coletas com intervalo
    tipo_coleta = Column(Enum(TipoColeta), default=TipoColeta.campo)
    coletor_principal = Column(String(200))
    coletores_adicionais = Column(JSONB, default=list)
    numero_campo = Column(String(100))  # número dado em campo pelo coletor

    # Localização
    localidade_id = Column(Integer, ForeignKey("localidades_geograficas.id"))
    localidade = relationship("LocalidadeGeografica", back_populates="especimes")

    # Descrição do espécime
    sexo = Column(String(20))
    estagio_vida = Column(String(50))  # adulto, juvenil, larva, etc.
    condicao = Column(String(100))  # estado de conservação
    numero_individuos = Column(Integer, default=1)
    descricao_morfologica = Column(Text)
    observacoes = Column(Text)
    habitat = Column(Text)

    # Identificação
    identificado_por = Column(String(200))
    data_identificacao = Column(DateTime)
    metodo_identificacao = Column(String(200))
    nivel_confianca_id = Column(String(50))  # ex: "alta", "média", "baixa"
    voucher_genbank = Column(String(100))

    # Curadoria / armazenamento
    status = Column(Enum(StatusEspecime), default=StatusEspecime.ativo)
    localizacao_fisica = Column(String(200))  # ex: "Gaveta 3, Caixa 12"
    meio_preservacao = Column(String(100))  # fixado em etanol, seco, etc.
    data_entrada_colecao = Column(DateTime, default=datetime.utcnow)

    # Darwin Core extras
    dwc_record_id = Column(String(200), unique=True, index=True)
    dwc_dataset_id = Column(String(200))
    referencias_bibliograficas = Column(JSONB, default=list)
    direitos = Column(String(200), default="CC BY 4.0")
    licenca = Column(String(200))

    # Metadados
    cadastrado_por_id = Column(Integer, ForeignKey("usuarios.id"))
    cadastrado_por_usuario = relationship("Usuario", back_populates="especimes_cadastrados")
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    imagens = relationship("ImagemEspecime", back_populates="especime", cascade="all, delete-orphan")
    emprestimos = relationship("Emprestimo", back_populates="especime")

    __table_args__ = (
        Index("ix_especime_codigo_catalogo", "codigo_catalogo"),
        Index("ix_especime_data_coleta", "data_coleta"),
        Index("ix_especime_status", "status"),
    )


class ImagemEspecime(Base):
    __tablename__ = "imagens_especimes"

    id = Column(Integer, primary_key=True, index=True)
    especime_id = Column(Integer, ForeignKey("especimes.id", ondelete="CASCADE"), nullable=False)
    especime = relationship("Especime", back_populates="imagens")

    nome_arquivo = Column(String(300), nullable=False)
    caminho = Column(String(500), nullable=False)
    url_relativa = Column(String(500))
    tipo_mime = Column(String(100))
    tamanho_bytes = Column(Integer)
    largura_px = Column(Integer)
    altura_px = Column(Integer)
    descricao = Column(String(500))
    is_principal = Column(Boolean, default=False)
    criado_em = Column(DateTime, default=datetime.utcnow)


class Emprestimo(Base):
    __tablename__ = "emprestimos"

    id = Column(Integer, primary_key=True, index=True)
    especime_id = Column(Integer, ForeignKey("especimes.id"), nullable=False)
    especime = relationship("Especime", back_populates="emprestimos")

    responsavel_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    responsavel = relationship("Usuario", back_populates="emprestimos")

    instituicao_destino = Column(String(300), nullable=False)
    pesquisador_responsavel = Column(String(200), nullable=False)
    finalidade = Column(Text)
    data_saida = Column(DateTime, nullable=False)
    data_prevista_retorno = Column(DateTime)
    data_retorno = Column(DateTime)
    observacoes = Column(Text)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
