from datetime import datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException, UploadFile
from fastapi.testclient import TestClient

from app.core.security import get_current_user
from app.main import app
from app.models.models import PerfilUsuario
from app.schemas.schemas import UsuarioOut
from app.services.imagem_service import ImagemService


def _client_for(perfil: PerfilUsuario = PerfilUsuario.leitor) -> TestClient:
    async def fake_current_user():
        return SimpleNamespace(id=1, perfil=perfil, ativo=True)

    app.dependency_overrides[get_current_user] = fake_current_user
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


def test_leitor_nao_cria_edita_ou_remove_especime():
    client = _client_for()
    assert client.post("/api/v1/especimes", json={}).status_code == 403
    assert client.put("/api/v1/especimes/1", json={}).status_code == 403
    assert client.delete("/api/v1/especimes/1").status_code == 403


def test_leitor_nao_edita_taxonomia_ou_localidade():
    client = _client_for()
    assert client.put("/api/v1/taxonomias/1", json={"nome_cientifico": "Teste"}).status_code == 403
    assert client.put("/api/v1/localidades/1", json={"pais": "Brasil"}).status_code == 403


def test_usuario_comum_nao_altera_ativo_ou_perfil():
    client = _client_for()
    response = client.put(
        "/api/v1/usuarios/1",
        json={"ativo": False, "perfil": "administrador"},
    )
    assert response.status_code == 403


def test_leitor_nao_exporta_dwca():
    client = _client_for()
    assert client.post("/api/v1/especimes/exportar/dwca", json={"ids": [1]}).status_code == 403
    assert client.get("/api/v1/especimes/exportar/dwca/todos").status_code == 403


def test_usuario_out_nao_quebra_com_email_legado_local():
    usuario = SimpleNamespace(
        id=1,
        nome="Administrador",
        email="admin@bioacervo.local",
        perfil=PerfilUsuario.administrador,
        ativo=True,
        criado_em=datetime.utcnow(),
    )

    assert UsuarioOut.model_validate(usuario).email == "admin@bioacervo.local"


@pytest.mark.asyncio
async def test_upload_rejeita_arquivo_que_nao_e_imagem():
    upload = UploadFile(filename="fake.jpg", file=__import__("io").BytesIO(b"not an image"))

    with pytest.raises(HTTPException) as exc:
        await ImagemService.upload(SimpleNamespace(), 1, upload)

    assert getattr(exc.value, "status_code", None) == 400
