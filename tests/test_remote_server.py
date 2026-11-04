"""Testes do servidor HTTP: auth, Range, ETag, auditoria e limites."""

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from cecilia.remote.auth import KeyStore
from cecilia.remote.publish import publish
from cecilia.remote.server import create_app
from cecilia.remote.settings import Settings

PEPPER = "p" * 48


@pytest.fixture
def cenario(layout, gravar_parquet, tmp_path):
    origem = tmp_path / "entrada"
    gravar_parquet(origem / "gaia.parquet", [1, 2, 3])
    resultado = publish(layout, origem, "gaia_teste", "v1")
    chave = KeyStore(layout, PEPPER).create("luan", 90)
    app = create_app(
        Settings(
            layout=layout,
            pepper=PEPPER,
            catalog_per_minute=1000,
            blob_per_minute=1000,
            global_per_minute=1000,
        )
    )
    return SimpleNamespace(
        layout=layout,
        resultado=resultado,
        blob=resultado.manifest.files[0].blob,
        chave=chave,
        app=app,
        client=TestClient(app),
        auth={"Authorization": f"Bearer {chave.token}"},
    )


def test_health_sem_chave(cenario):
    resposta = cenario.client.get("/health")

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "ok"
    assert cenario.app.state.audit.recent() == []


def test_catalogo_exige_chave(cenario):
    resposta = cenario.client.get("/v1/catalog")

    assert resposta.status_code == 401
    assert resposta.headers["www-authenticate"].lower() == "bearer"
    registro = cenario.app.state.audit.recent(limit=1)[0]
    assert registro["action"] == "auth"
    assert registro["status"] == 401
    assert registro["alias"] is None


def test_catalogo_e_304(cenario):
    resposta = cenario.client.get("/v1/catalog", headers=cenario.auth)

    assert resposta.status_code == 200
    assert resposta.json()["datasets"][0]["name"] == "gaia_teste"
    etag = resposta.headers["etag"]
    assert etag

    segunda = cenario.client.get(
        "/v1/catalog",
        headers={**cenario.auth, "If-None-Match": etag},
    )
    assert segunda.status_code == 304
    assert segunda.content == b""


def test_manifesto_e_304(cenario):
    url = "/v1/datasets/gaia_teste/versions/v1"
    resposta = cenario.client.get(url, headers=cenario.auth)

    assert resposta.status_code == 200
    assert resposta.json()["version"] == "v1"

    segunda = cenario.client.get(
        url,
        headers={**cenario.auth, "If-None-Match": resposta.headers["etag"]},
    )
    assert segunda.status_code == 304


def test_blob_completo_e_auditoria(cenario):
    url = f"/v1/blobs/{cenario.blob}"
    resposta = cenario.client.get(url, headers=cenario.auth)

    assert resposta.status_code == 200
    assert resposta.content == (cenario.layout.blobs / cenario.blob).read_bytes()
    assert resposta.headers["etag"] == f'"{cenario.blob}"'
    assert resposta.headers["accept-ranges"] == "bytes"

    registro = cenario.app.state.audit.recent(limit=1)[0]
    assert registro["action"] == "blob"
    assert registro["alias"] == "luan"
    assert registro["dataset"] == "gaia_teste"
    assert registro["version"] == "v1"
    assert registro["file"] == "gaia.parquet"
    assert registro["bytes_sent"] == len(resposta.content)
    assert registro["status"] == 200


def test_blob_com_range(cenario):
    url = f"/v1/blobs/{cenario.blob}"
    resposta = cenario.client.get(
        url,
        headers={**cenario.auth, "Range": "bytes=0-9"},
    )

    assert resposta.status_code == 206
    assert len(resposta.content) == 10
    assert resposta.headers["content-range"].startswith("bytes 0-9/")

    registro = cenario.app.state.audit.recent(limit=1)[0]
    assert registro["bytes_sent"] == 10


def test_blob_e_304(cenario):
    url = f"/v1/blobs/{cenario.blob}"
    primeira = cenario.client.get(url, headers=cenario.auth)
    segunda = cenario.client.get(
        url,
        headers={**cenario.auth, "If-None-Match": primeira.headers["etag"]},
    )

    assert segunda.status_code == 304
    assert segunda.content == b""


def test_blob_nao_publicado(cenario):
    orfao = "a" * 64
    (cenario.layout.blobs / orfao).write_bytes(b"x")

    resposta = cenario.client.get(f"/v1/blobs/{orfao}", headers=cenario.auth)
    assert resposta.status_code == 404


def test_blob_com_hash_invalido(cenario):
    resposta = cenario.client.get("/v1/blobs/nao-e-hash", headers=cenario.auth)
    assert resposta.status_code == 404


def test_dataset_desconhecido(cenario):
    resposta = cenario.client.get(
        "/v1/datasets/nao_existe/versions/v1",
        headers=cenario.auth,
    )
    assert resposta.status_code == 404


def test_whoami(cenario):
    resposta = cenario.client.get("/v1/whoami", headers=cenario.auth)

    assert resposta.status_code == 200
    assert resposta.json()["alias"] == "luan"
    assert resposta.json()["key_id"] == cenario.chave.key_id


def test_chave_revogada(cenario):
    assert cenario.app.state.keys.revoke(cenario.chave.key_id)
    resposta = cenario.client.get("/v1/catalog", headers=cenario.auth)
    assert resposta.status_code == 401


def test_chave_expirada(cenario):
    expirada = cenario.app.state.keys.create("maria", 0)
    resposta = cenario.client.get(
        "/v1/catalog",
        headers={"Authorization": f"Bearer {expirada.token}"},
    )
    assert resposta.status_code == 401


def test_limite_por_chave(cenario):
    app = create_app(
        Settings(
            layout=cenario.layout,
            pepper=PEPPER,
            catalog_per_minute=1000,
            blob_per_minute=2,
            global_per_minute=1000,
        )
    )
    cliente = TestClient(app)
    url = f"/v1/blobs/{cenario.blob}"

    assert cliente.get(url, headers=cenario.auth).status_code == 200
    assert cliente.get(url, headers=cenario.auth).status_code == 200
    resposta = cliente.get(url, headers=cenario.auth)
    assert resposta.status_code == 429

    registro = app.state.audit.recent(limit=1)[0]
    assert registro["action"] == "rate-limit"


def test_sem_rota_administrativa(cenario):
    resposta = cenario.client.get("/v1/admin/keys", headers=cenario.auth)

    assert resposta.status_code == 404
    registro = cenario.app.state.audit.recent(limit=1)[0]
    assert registro["action"] == "http"
