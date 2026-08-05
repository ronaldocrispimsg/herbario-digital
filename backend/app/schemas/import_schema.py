from pydantic import BaseModel, Field
from typing import Optional, List

class ImportedRowSchema(BaseModel):
    sheet: str
    row_index: int
    codigo: str
    nome_cientifico: str
    nome_popular: Optional[str] = None
    filo: Optional[str] = None
    classe: Optional[str] = None
    ordem: Optional[str] = None
    familia: Optional[str] = None
    genero: Optional[str] = None
    especie: Optional[str] = None
    localizacao: Optional[str] = None
    data_coleta: Optional[str] = None
    origem: Optional[str] = None
    coletor: Optional[str] = None
    status_validacao: str = "valid"  # valid, warning, error
    mensagem_validacao: Optional[str] = None

class ImportPreviewResponse(BaseModel):
    filename: str
    total_rows: int
    valid_rows: int
    warning_rows: int
    error_rows: int
    new_taxonomias_est: int
    new_localidades_est: int
    rows: List[ImportedRowSchema]

class ImportExecuteRequest(BaseModel):
    rows: List[ImportedRowSchema]

class ImportExecuteResponse(BaseModel):
    total_processed: int
    especimes_criados: int
    especimes_atualizados: int
    taxonomias_criadas: int
    localidades_criadas: int
    erros: int
    detalhes_erros: List[str] = []
