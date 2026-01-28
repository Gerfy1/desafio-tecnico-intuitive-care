from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_read_main():
    """teste pra verificar se a API inicia e a documentação tá acessível!"""
    response = client.get("/docs")
    assert response.status_code == 200

def test_listar_operadoras():
    """testa a rota de listagem (Paginação e Formato)"""
    response = client.get("/api/operadoras?page=1&limit=5")
    assert response.status_code == 200
    json_data = response.json()
    
    # Valida estrutura da resposta
    assert "data" in json_data
    assert "total" in json_data
    assert len(json_data["data"]) <= 5

def test_estatisticas():
    """testa se a rota de estatísticas retorna a lista corretamente"""
    response = client.get("/api/estatisticas")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_busca_inexistente():
    """Testa busca por algo que nao existe (deve retornar lista vazia, e nao um erro)"""
    response = client.get("/api/operadoras?search=XPTO_NAO_EXISTE")
    assert response.status_code == 200
    assert len(response.json()["data"]) == 0