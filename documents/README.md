# Sistema de Conciliação de Fornecedores

Sistema completo para conciliação interna de Razão de Fornecedores (Contas a Pagar), desenvolvido com **FastAPI** (Backend) e **React + TypeScript** (Frontend).

## 📋 Funcionalidades

### ✅ Processamento Automático
- Upload de PDF/ZIP do Razão de Fornecedores
- Extração automática de 57 páginas de dados estruturados
- Parsing inteligente de lançamentos (data, lote, histórico, valores)
- Identificação automática de NFs, CNPJs e tipos de operação

### ✅ Conciliação Inteligente
- **Matching por NF**: Vincula pagamentos às compras pela NF mencionada
- **Matching por Valor Exato**: Identifica pagamentos com valor idêntico à compra
- **Matching FIFO**: Distribui pagamentos nas compras mais antigas (First In, First Out)
- Cálculo automático de saldo devedor por fornecedor

### ✅ Validações Contábeis
- Recalcula saldos passo a passo e detecta divergências
- Valida partidas dobradas (Total Crédito vs Total Débito)
- Identifica saldos negativos e pagamentos sem compra correspondente
- Gera relatório de auditoria completo

### ✅ Interface Moderna
- Dashboard com resumo executivo
- Filtros por status (Quitado, Em Aberto, Adiantado)
- Detalhamento completo por fornecedor
- Listagem de compras não quitadas
- Exportação para Excel (completo, em aberto, divergências)

---

## 🚀 Como Executar

### Pré-requisitos
- Docker e Docker Compose instalados
- Porta 3000 (frontend), 8000 (backend) e 5432 (banco) disponíveis

### Inicialização

1. **Clone ou extraia o projeto**:
```bash
cd conciliacao-fornecedores
```

2. **Inicie os serviços com Docker Compose**:
```bash
docker-compose up --build
```

3. **Aguarde a inicialização** (leva ~2 minutos na primeira vez):
   - ✅ PostgreSQL: porta 5432
   - ✅ Backend (FastAPI): porta 8000
   - ✅ Frontend (React): porta 3000

4. **Acesse o sistema**:
   - **Frontend**: http://localhost:3000
   - **API Docs**: http://localhost:8000/docs
   - **Health Check**: http://localhost:8000/health

---

## 📖 Como Usar

### 1. Upload do Arquivo

1. Acesse http://localhost:3000
2. Clique em **"Importar PDF"**
3. Selecione o arquivo `Razão_Forn_2025.pdf`
4. Aguarde o processamento (30-60 segundos)

O sistema irá:
- ✅ Extrair todos os fornecedores e lançamentos
- ✅ Validar integridade contábil
- ✅ Executar conciliação automática
- ✅ Gerar estatísticas e relatórios

### 2. Visualizar Resumo

Após o processamento, você verá:

```
┌─────────────────────────────────────────────────────┐
│ RESUMO GERAL                                        │
├─────────────────────────────────────────────────────┤
│ Total de Fornecedores: 156                          │
│ Fornecedores Quitados: 89                           │
│ Fornecedores em Aberto: 65                          │
│ Valor Total a Pagar: R$ 245.678,90                  │
└─────────────────────────────────────────────────────┘
```

### 3. Consultar Fornecedores

- **Filtrar por status**: Use o dropdown para ver apenas quitados, em aberto ou adiantados
- **Clicar em um fornecedor**: Abre modal detalhado com:
  - Total de compras e pagamentos
  - Saldo devedor atual
  - Lista de compras não quitadas (com NF, valor total, valor pago e saldo)

### 4. Exportar Relatórios

- **Excel - Em Aberto**: Apenas fornecedores com saldo devedor
- **Excel - Completo**: Todos os fornecedores
- **Excel - Divergências**: Apenas fornecedores com erros contábeis

---

## 🏗️ Arquitetura

### Backend (FastAPI + Python)

```
backend/
├── main.py              # API REST (endpoints)
├── models.py            # Modelos SQLAlchemy
├── parser.py            # Extração do PDF
├── conciliacao.py       # Algoritmo de matching
├── database.py          # Configuração do banco
├── requirements.txt     # Dependências Python
└── Dockerfile
```

**Principais Endpoints**:
- `POST /upload` - Upload e processamento do arquivo
- `GET /resumo/{arquivo_id}` - Resumo geral
- `GET /fornecedores` - Lista fornecedores (com filtros)
- `GET /fornecedores/{id}` - Detalhes completos de um fornecedor
- `GET /divergencias` - Lista divergências contábeis
- `GET /export/excel/{arquivo_id}` - Exporta para Excel

### Frontend (React + TypeScript)

```
frontend/
├── src/
│   ├── App.tsx                  # Componente principal
│   ├── main.tsx                 # Entry point
│   ├── index.css                # Estilos Tailwind
│   └── services/
│       └── api.ts               # Cliente HTTP (Axios)
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── Dockerfile
```

**Componentes Principais**:
- **Dashboard**: Resumo executivo com cards de estatísticas
- **Tabela de Fornecedores**: Listagem interativa com filtros
- **Modal de Detalhes**: Drill-down completo do fornecedor
- **Upload**: Interface de importação de arquivos

### Banco de Dados (PostgreSQL)

```sql
Tabelas Principais:
├── arquivo_importado     # Arquivos processados
├── fornecedor            # Contas de fornecedores
├── lancamento_fornecedor # Lançamentos individuais
├── conciliacao_interna   # Vínculos crédito/débito
└── divergencia           # Erros encontrados
```

---

## 🔍 Algoritmo de Conciliação

### 1. Extração e Classificação

```python
Para cada lançamento:
  - Se valor_credito > 0 → COMPRA
  - Se valor_debito > 0 → PAGAMENTO
  - Extrair número de NF do histórico (regex)
```

### 2. Matching (3 Estratégias)

**Estratégia 1 - Matching por NF (confiança 95%)**:
```python
Se pagamento menciona "NF 21100":
  → Vincular à compra da NF 21100
```

**Estratégia 2 - Valor Exato (confiança 90%)**:
```python
Se valor do pagamento = valor da compra:
  → Vincular 1:1
```

**Estratégia 3 - FIFO (confiança 70%)**:
```python
Para cada pagamento:
  → Abater das compras mais antigas até esgotar o valor
```

### 3. Validação de Integridade

```python
Para cada fornecedor:
  - Recalcular saldo: Saldo_Anterior + Σ_Créditos - Σ_Débitos
  - Comparar com saldo registrado
  - Se divergência > R$ 0,02 → Marcar como erro
```

---

## 📊 Relatórios Gerados

### 1. Fornecedores em Aberto
Lista apenas fornecedores com saldo devedor, ordenados por valor.

| Fornecedor | Total Compras | Total Pagtos | Saldo a Pagar | NFs Pendentes |
|-----------|---------------|--------------|---------------|---------------|
| LOTUS COM | R$ 36.994,05  | R$ 23.437,67 | R$ 13.556,38  | 3             |
| ELETINTAS | R$ 8.500,50   | R$ 6.000,00  | R$ 2.500,50   | 1             |

### 2. Compras Não Quitadas (por fornecedor)
Detalha quais NFs ainda não foram pagas completamente.

| Data       | NF     | Valor Total   | Pago          | Pendente      | Status   |
|-----------|--------|---------------|---------------|---------------|----------|
| 04/09/2025| 341711 | R$ 12.689,10  | R$ 4.568,90   | R$ 8.120,20   | PARCIAL  |
| 18/08/2025| 336853 | R$ 2.816,10   | R$ 1.281,44   | R$ 1.534,66   | PARCIAL  |

### 3. Divergências Contábeis
Identifica erros de cálculo ou inconsistências.

| Fornecedor  | Problema                          | Diferença   |
|------------|-----------------------------------|-------------|
| GURGELMIX  | Saldo calculado diverge           | R$ 0,02     |
| INTERASIA  | Pagamento maior que compra        | R$ 100,00   |

---

## 🛠️ Tecnologias Utilizadas

### Backend
- **FastAPI** 0.109 - Framework web moderno
- **SQLAlchemy** 2.0 - ORM para PostgreSQL
- **Pydantic** 2.5 - Validação de dados
- **OpenPyXL** 3.1 - Exportação para Excel
- **Python-Levenshtein** 0.23 - Similaridade de texto

### Frontend
- **React** 18.2 - Biblioteca UI
- **TypeScript** 5.3 - Tipagem estática
- **Vite** 5.0 - Build tool
- **Tailwind CSS** 3.4 - Framework CSS
- **Axios** 1.6 - Cliente HTTP
- **Lucide React** - Ícones

### Infraestrutura
- **PostgreSQL** 15 - Banco de dados
- **Docker** + **Docker Compose** - Containerização

---

## 📝 Casos de Uso Reais

### Exemplo 1: LOTUS COMERCIAL

**Situação**: 
- Total de compras: R$ 36.994,05
- Total de pagamentos: R$ 23.437,67
- Saldo devedor: R$ 13.556,38

**Compras não quitadas**:
1. NF 341711 (04/09): R$ 12.689,10 → Pago R$ 4.568,90 → **Faltam R$ 8.120,20**
2. NF 336853 (18/08): R$ 2.816,10 → Pago R$ 1.281,44 → **Faltam R$ 1.534,66**
3. NF 305865 (28/03): R$ 5.535,20 → Pago R$ 1.633,46 → **Faltam R$ 3.901,74**

**Ação Sugerida**: Priorizar quitação da NF 305865 (mais antiga).

### Exemplo 2: F I CALDEIRARIA

**Situação**:
- Total de compras: R$ 10.207,66
- Total de pagamentos: R$ 10.207,66
- Saldo devedor: **R$ 0,00** ✅

**Status**: QUITADO - Todos os pagamentos foram conciliados com sucesso.

---

## 🔧 Configuração Avançada

### Variáveis de Ambiente

Edite o `docker-compose.yml` para customizar:

```yaml
services:
  backend:
    environment:
      DATABASE_URL: postgresql://usuario:senha@host:porta/banco
      DEBUG: false
      
  frontend:
    environment:
      VITE_API_URL: http://seu-backend:8000
```

### Alterar Portas

```yaml
services:
  frontend:
    ports:
      - "8080:3000"  # Expor na porta 8080 ao invés de 3000
```

---

## 🐛 Troubleshooting

### Erro: "Porta 5432 já em uso"

```bash
# Parar PostgreSQL local
sudo systemctl stop postgresql

# Ou alterar porta no docker-compose.yml:
ports:
  - "5433:5432"
```

### Erro: "Arquivo já foi importado"

O sistema detecta duplicação via hash SHA256. Para reprocessar:
```bash
# Parar containers
docker-compose down

# Limpar volume do banco
docker volume rm conciliacao-fornecedores_postgres_data

# Reiniciar
docker-compose up --build
```

### Frontend não conecta ao Backend

Verifique se o proxy está configurado em `vite.config.ts`:
```typescript
proxy: {
  '/api': {
    target: 'http://backend:8000',
    changeOrigin: true,
  }
}
```

---

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique os logs: `docker-compose logs -f backend`
2. Acesse a documentação da API: http://localhost:8000/docs
3. Teste o health check: http://localhost:8000/health

---

## 📄 Licença

Este projeto foi desenvolvido para fins de conciliação contábil interna.

---

**Desenvolvido com ❤️ usando FastAPI + React + PostgreSQL**
