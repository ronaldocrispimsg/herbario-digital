from datetime import datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException, UploadFile
from fastapi.testclient import TestClient

from app.config.security import get_current_user
from app.routes.endpoints import auth as auth_route
from app.routes.endpoints import usuarios_emprestimos as emprestimos_route
from main import app
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


def test_listar_emprestimos_nao_quebra_com_banco_vazio():
    client = _client_for(PerfilUsuario.administrador)
    response = client.get("/api/v1/emprestimos?page=1&per_page=20")
    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_auth_endpoints_verificam_erros_basicos():
    client = _client_for()
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 200
    assert response.json()["id"] == 1

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "naoexiste@bioacervo.local", "password": "senhaerrada"},
    )
    assert response.status_code == 401


def test_registrar_pode_ser_usado_sem_administrador(monkeypatch):
    async def fake_get_db():
        yield object()

    async def fake_get_by_email(db, email):
        return None

    async def fake_create(db, data):
        return SimpleNamespace(
            id=2,
            nome=data.nome,
            email=data.email,
            perfil=data.perfil,
            ativo=True,
            criado_em=datetime.utcnow(),
        )

    monkeypatch.setattr(auth_route, "get_db", fake_get_db)
    monkeypatch.setattr(auth_route.UsuarioService, "get_by_email", fake_get_by_email)
    monkeypatch.setattr(auth_route.UsuarioService, "create", fake_create)

    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/registrar",
        json={
            "nome": "Novo Usuário",
            "email": "novo@bioacervo.local",
            "senha": "Senha123",
        },
    )

    assert response.status_code == 201
    assert response.json()["email"] == "novo@bioacervo.local"


def test_especimes_endpoints_tratam_erros_sem_500():
    client = _client_for(PerfilUsuario.administrador)
    assert client.get("/api/v1/especimes").status_code == 200
    assert client.post("/api/v1/especimes/buscar", json={"page": 1, "per_page": 20}).status_code == 200
    assert client.get("/api/v1/especimes/999999").status_code == 404
    assert client.post("/api/v1/especimes", json={}).status_code == 422
    assert client.put("/api/v1/especimes/999999", json={"observacoes": "teste"}).status_code == 404
    assert client.delete("/api/v1/especimes/999999").status_code == 404


def test_taxonomia_e_localidade_endpoints_tratam_erros():
    client = _client_for(PerfilUsuario.administrador)
    assert client.get("/api/v1/taxonomias").status_code == 200
    assert client.post("/api/v1/taxonomias", json={}).status_code == 422
    assert client.get("/api/v1/taxonomias/999999").status_code == 404
    assert client.put("/api/v1/taxonomias/999999", json={"nome_cientifico": "Teste"}).status_code == 404
    assert client.delete("/api/v1/taxonomias/999999").status_code == 404

    assert client.get("/api/v1/localidades").status_code == 200
    assert client.post("/api/v1/localidades", json={}).status_code == 422
    assert client.get("/api/v1/localidades/999999").status_code == 404
    assert client.put("/api/v1/localidades/999999", json={"pais": "Brasil"}).status_code == 404
    assert client.delete("/api/v1/localidades/999999").status_code == 404


def test_usuarios_e_emprestimos_endpoints_tratam_erros():
    client = _client_for(PerfilUsuario.administrador)
    assert client.get("/api/v1/usuarios").status_code == 200
    assert client.get("/api/v1/usuarios/999999").status_code == 404
    assert client.post("/api/v1/usuarios", json={}).status_code == 422
    assert client.put("/api/v1/usuarios/999999", json={"nome": "Teste"}).status_code == 404
    assert client.delete("/api/v1/usuarios/999999").status_code == 404

    assert client.get("/api/v1/emprestimos").status_code == 200
    assert client.post("/api/v1/emprestimos", json={}).status_code == 422
    assert client.post(
        "/api/v1/emprestimos",
        json={
            "especime_id": 999999,
            "instituicao_destino": "Instituição Teste",
            "pesquisador_responsavel": "Pesquisador Teste",
            "data_saida": "2026-06-29T10:00:00",
        },
    ).status_code == 404
    assert client.put("/api/v1/emprestimos/999999", json={"observacoes": "teste"}).status_code == 404


def test_criar_emprestimo_retorna_201_quando_especime_esta_associado(monkeypatch):
    async def fake_get_db():
        class FakeSession:
            def add(self, obj):
                self.added = obj

            async def flush(self):
                return None

            async def refresh(self, obj, attribute=None):
                return None

        yield FakeSession()

    async def fake_get_by_id(db, especime_id):
        return SimpleNamespace(id=especime_id, codigo_catalogo="TEST-1", status="ativo")

    monkeypatch.setattr(emprestimos_route, "get_db", fake_get_db)
    monkeypatch.setattr(emprestimos_route.EspecimeService, "get_by_id", fake_get_by_id)

    client = _client_for(PerfilUsuario.administrador)
    response = client.post(
        "/api/v1/emprestimos",
        json={
            "especime_id": 1,
            "instituicao_destino": "Instituição Teste",
            "pesquisador_responsavel": "Pesquisador Teste",
            "data_saida": "2026-06-29T10:00:00",
        },
    )

    assert response.status_code == 201
    assert response.json()["especime"]["id"] == 1


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
