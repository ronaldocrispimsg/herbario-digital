import io
import pytest
from types import SimpleNamespace
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_current_user
from app.models.models import PerfilUsuario
from app.services.import_service import ImportService


def _client_for(perfil: PerfilUsuario = PerfilUsuario.curador) -> TestClient:
    async def fake_current_user():
        return SimpleNamespace(id=1, perfil=perfil, ativo=True)

    app.dependency_overrides[get_current_user] = fake_current_user
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


def test_leitor_nao_acessa_importacao():
    client = _client_for(perfil=PerfilUsuario.leitor)
    res_preview = client.post("/api/v1/import/preview", files={"file": ("test.csv", b"codigo,nome_cientifico\nHERB-1,Tabebuia rosea")})
    assert res_preview.status_code == 403

    res_exec = client.post("/api/v1/import/execute", json={"rows": []})
    assert res_exec.status_code == 403


def test_preview_importacao_csv_sucesso():
    client = _client_for(perfil=PerfilUsuario.curador)
    csv_content = (
        "codigo,nome_cientifico,familia,localizacao,coletor,data_coleta\n"
        "HERB-0001,Handroanthus chrysotrichus,Bignoniaceae,Belo Horizonte,Silva J.,2024-05-10\n"
        "HERB-0002,Tabebuia rosea,Bignoniaceae,Sabará,Santos M.,2024-06-12\n"
    ).encode("utf-8")

    response = client.post(
        "/api/v1/import/preview",
        files={"file": ("amostras.csv", io.BytesIO(csv_content), "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "amostras.csv"
    assert data["total_rows"] == 2
    assert data["valid_rows"] == 2
    assert len(data["rows"]) == 2
    assert data["rows"][0]["codigo"] == "HERB-0001"
    assert data["rows"][0]["nome_cientifico"] == "Handroanthus chrysotrichus"


def test_parse_and_validate_file_warning_duplicados():
    csv_content = (
        "codigo,nome_cientifico\n"
        "HERB-0001,Handroanthus chrysotrichus\n"
        "HERB-0001,Tabebuia rosea\n"
    ).encode("utf-8")

    preview = ImportService.parse_and_validate_file(csv_content, "duplicados.csv")
    assert preview.total_rows == 2
    assert preview.warning_rows == 1
    assert preview.rows[1].status_validacao == "warning"
