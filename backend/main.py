from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from backend import database

app = FastAPI(
    title="API Intuitive Care - Teste Técnico",
    description="API para consulta de dados de operadoras e despesas da ANS",
    version="1.0.0"
)

origins = [
    "http://localhost:5173", #cors do frontend
    "http://127.0.0.1:5173",
    "*" 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

# --- schemas (Modelos de Resposta pydantic) ---
# aqui define O QUE o frontend vai receber de volta (Segurança e Documentação)

class OperadoraDTO(BaseModel):
    registro_ans: str
    cnpj: Optional[str]
    razao_social: Optional[str]
    uf: Optional[str]
    modalidade: Optional[str]
    
    model_config = ConfigDict(from_attributes=True) #permissao pra ler direto do objeto SQLAlchemy

class DespesaDTO(BaseModel):
    ano: int
    trimestre: str
    conta: str
    valor: float

class EstatisticaDTO(BaseModel):
    razao_social: str
    uf: str
    valor_total: float
    media_trimestral: float
    desvio_padrao: float
    qtd_trimestres: int

class PaginatedResponse(BaseModel):
    data: List[OperadoraDTO]
    total: int
    page: int
    limit: int

# --- rotas ---

@app.get("/api/operadoras", response_model=PaginatedResponse)
def listar_operadoras(
    page: int = Query(1, ge=1, description="Número da página"),
    limit: int = Query(10, ge=1, le=100, description="Itens por página"),
    search: Optional[str] = Query(None, description="Busca por Razão Social ou CNPJ"),
    db: Session = Depends(database.get_db)
):
    """
    lista todas as operadoras com paginaçao e busca (SQL LIKE)
    """
    offset = (page - 1) * limit
    
    # query Base
    sql_query = "SELECT * FROM dim_operadoras WHERE 1=1"
    params = {}
    
    # filtro de busca (case insensitive no PostgreSQL usa ILIKE)
    if search:
        sql_query += " AND (razao_social ILIKE :search OR cnpj LIKE :search)"
        params['search'] = f"%{search}%"
    
    #contagem Total (para a paginaçao funcionar no front)
    count_sql = f"SELECT COUNT(*) FROM ({sql_query}) as total"
    total = db.execute(text(count_sql), params).scalar()
    
    #busca Paginada
    sql_query += " ORDER BY razao_social LIMIT :limit OFFSET :offset"
    params['limit'] = limit
    params['offset'] = offset
    
    result = db.execute(text(sql_query), params).mappings().all()
    
    return {
        "data": result,
        "total": total,
        "page": page,
        "limit": limit
    }

@app.get("/api/operadoras/{identificador}")
def detalhes_operadora(identificador: str, db: Session = Depends(database.get_db)):
    """
    busca operadora por Registro ANS ou CNPJ
    """
    #tenta buscar por Registro ANS
    sql = "SELECT * FROM dim_operadoras WHERE registro_ans = :id OR cnpj = :id"
    result = db.execute(text(sql), {'id': identificador}).mappings().first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Operadora não encontrada")
    
    return result

@app.get("/api/operadoras/{registro_ans}/despesas", response_model=List[DespesaDTO])
def historico_despesas(registro_ans: str, db: Session = Depends(database.get_db)):
    """
    retorna o histórico de despesas de uma operadora
    """
    #ordena por Ano/Trimestre mais recente
    sql = """
        SELECT ano, trimestre, conta, valor 
        FROM fato_despesas 
        WHERE registro_ans = :reg 
        ORDER BY ano DESC, trimestre DESC
    """
    result = db.execute(text(sql), {'reg': registro_ans}).mappings().all()
    
    return result

@app.get("/api/estatisticas", response_model=List[EstatisticaDTO])
def obter_estatisticas(db: Session = Depends(database.get_db)):
    """
    retorna o Top 5 operadoras com maiores despesas (Pré-calculado no ETL)
    Estratégia: Leitura direta da tabela 'analise_agregada' para performance máxima
    """
    sql = "SELECT * FROM analise_agregada ORDER BY valor_total DESC LIMIT 10"
    result = db.execute(text(sql)).mappings().all()
    
    return result