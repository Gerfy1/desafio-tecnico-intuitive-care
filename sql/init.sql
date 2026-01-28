-- criaçao das tabelas para o Teste ANS

-- kustificativa da ,odelagem (Star Schema):
-- optei por separar dados cadastrais (Dimensão) dos dados de despesas (Fato)
-- isso evita redundância de strings (Razão Social, UF e afins) repetidas milhoes de vezes 
-- na tabela de despesas, economizando armazenamento e facilitando updates cadastrais

CREATE TABLE IF NOT EXISTS dim_operadoras (
    registro_ans VARCHAR(10) PRIMARY KEY,
    cnpj VARCHAR(20),
    razao_social TEXT,
    uf VARCHAR(2),
    modalidade TEXT
);

CREATE INDEX idx_operadoras_uf ON dim_operadoras(uf);

CREATE TABLE IF NOT EXISTS fato_despesas (
    id SERIAL PRIMARY KEY,
    registro_ans VARCHAR(10) REFERENCES dim_operadoras(registro_ans),
    ano INTEGER,
    trimestre VARCHAR(10),
    conta VARCHAR(50),
    valor NUMERIC(18, 2), -- DECIMAL para precisao monetaria exata
    
    -- constraint para garantir unicidade do registro se necessario
    -- (aqui é opcional, dependendo da granularidade dos dados)
    CONSTRAINT fk_operadora FOREIGN KEY (registro_ans) REFERENCES dim_operadoras(registro_ans)
);

-- indices para performance em queriees analiticas
CREATE INDEX idx_despesas_ano_trimestre ON fato_despesas(ano, trimestre);
CREATE INDEX idx_despesas_conta ON fato_despesas(conta);

-- tabela de agregacao 
-- tabela fisica para performance (Data Mart)
CREATE TABLE IF NOT EXISTS analise_agregada (
    razao_social TEXT,
    uf VARCHAR(2),
    valor_total NUMERIC(18, 2),
    media_trimestral NUMERIC(18, 2),
    desvio_padrao NUMERIC(18, 2),
    qtd_trimestres INTEGER
);