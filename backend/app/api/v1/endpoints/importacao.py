from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import get_current_user, require_roles
from app.models.models import PerfilUsuario
from app.schemas.import_schema import ImportPreviewResponse, ImportExecuteRequest, ImportExecuteResponse
from app.services.import_service import ImportService

router = APIRouter(prefix="/import", tags=["Importação de Planilhas"])


@router.post(
    "/preview",
    response_model=ImportPreviewResponse,
    summary="Pré-visualizar e validar planilha (Dry-Run)",
)
async def preview_import(
    file: UploadFile = File(...),
    current_user=Depends(require_roles(PerfilUsuario.administrador, PerfilUsuario.curador)),
):
    if not file.filename.lower().endswith((".xlsx", ".csv", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de arquivo inválido. Formatos suportados: .xlsx, .csv",
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O arquivo enviado está vazio.",
        )

    try:
        preview = ImportService.parse_and_validate_file(file_bytes, file.filename)
        return preview
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Erro ao processar planilha: {str(exc)}",
        )


@router.post(
    "/execute",
    response_model=ImportExecuteResponse,
    summary="Efetivar a importação de planilhas no banco de dados",
)
async def execute_import(
    request: ImportExecuteRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(PerfilUsuario.administrador, PerfilUsuario.curador)),
):
    if not request.rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhuma linha foi fornecida para importação.",
        )

    try:
        result = await ImportService.execute_import(db, request.rows, current_user.id)
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha ao executar importação: {str(exc)}",
        )
