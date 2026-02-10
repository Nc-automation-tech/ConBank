# 🚀 Guia Rápido de Início

## Passo 1: Iniciar o Sistema

```bash
cd conciliacao-fornecedores
./start.sh
```

**Ou manualmente**:
```bash
docker-compose up --build
```

## Passo 2: Acessar a Interface

Abra seu navegador em: **http://localhost:3000**

## Passo 3: Importar o Arquivo

1. Clique no botão **"Importar PDF"**
2. Selecione o arquivo `Razão_Forn_2025.pdf`
3. Aguarde o processamento (~30 segundos)

## Passo 4: Explorar os Resultados

### Dashboard Principal
- **Total de Fornecedores**: Visualize a quantidade total
- **Fornecedores Quitados**: Contas sem saldo devedor
- **Fornecedores em Aberto**: Contas com valores a pagar
- **Valor Total a Pagar**: Soma de todos os saldos devedores

### Tabela de Fornecedores
- **Filtrar por Status**: Use o dropdown para filtrar
- **Clicar em um Fornecedor**: Abre detalhes completos
- **Ver Compras Pendentes**: Identifica NFs não quitadas

### Exportar Relatórios
- **Excel - Em Aberto**: Lista apenas saldos devedores
- **Excel - Completo**: Todos os fornecedores
- **Excel - Divergências**: Apenas erros contábeis

---

## 📊 Interpretando os Resultados

### Status de Pagamento

| Status      | Significado                                    | Cor     |
|------------|------------------------------------------------|---------|
| ✅ QUITADO  | Total de pagamentos = Total de compras        | Verde   |
| ⚠️ EM_ABERTO | Total de pagamentos < Total de compras        | Amarelo |
| 🔴 ADIANTADO | Total de pagamentos > Total de compras        | Vermelho|

### Exemplo Prático

**Fornecedor: LOTUS COMERCIAL**
- Total Compras: R$ 36.994,05
- Total Pagamentos: R$ 23.437,67
- **Saldo a Pagar: R$ 13.556,38** ⚠️

**Compras Não Quitadas**:
1. NF 341711: Faltam R$ 8.120,20
2. NF 336853: Faltam R$ 1.534,66
3. NF 305865: Faltam R$ 3.901,74

---

## 🔧 Comandos Úteis

### Ver Logs
```bash
docker-compose logs -f
```

### Parar Sistema
```bash
docker-compose down
```

### Reiniciar Sistema
```bash
docker-compose restart
```

### Limpar Tudo (Banco de Dados Incluído)
```bash
docker-compose down -v
```

---

## 🆘 Problemas Comuns

### "Porta já em uso"
```bash
# Identifique qual processo está usando a porta
sudo lsof -i :3000  # ou :8000, :5432

# Pare o processo ou altere a porta no docker-compose.yml
```

### "Frontend não carrega"
Aguarde 1-2 minutos - o frontend leva um tempo para compilar na primeira vez.

### "Erro ao importar arquivo"
Verifique se o arquivo é o `Razão_Forn_2025.pdf` correto (formato ZIP com TXTs internos).

---

## 📞 Acesso Rápido

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Banco (PostgreSQL)**: localhost:5432
  - Usuário: `postgres`
  - Senha: `postgres`
  - Database: `conciliacao`

---

## 💡 Dicas

1. **Performance**: O sistema processa ~1.200 lançamentos em <1 minuto
2. **Memória**: Requer ~500MB de RAM
3. **Disco**: Ocupa ~200MB após instalação
4. **Conciliação**: Score de 90%+ indica alta confiança
5. **Auditoria**: Todos os matches são rastreáveis

---

**Pronto para usar! 🎉**
