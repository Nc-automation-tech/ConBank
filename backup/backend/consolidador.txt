"""
Pós-Processamento: Consolidação de Lançamentos
===============================================

PROBLEMA:
Quando uma NF é lançada em múltiplas contas de custo (CPCs diferentes),
o sistema contábil cria vários lançamentos para a mesma NF na mesma data.

Exemplo:
  NF 4316 (08/08/2025):
  - Lançamento 1: R$ 1.151,05 (CPC 1358)
  - Lançamento 2: R$    25,43 (CPC 1358)
  → Total NF: R$ 1.176,48

O parser extrai corretamente ambos os lançamentos, mas eles devem ser
CONSOLIDADOS em um único registro no banco de dados para que o FIFO
funcione corretamente.

SOLUÇÃO:
Após o parser extrair os lançamentos, consolidar por:
  - numero_nf + data_lancamento + tipo_operacao

IMPORTANTE:
- COMPRAS: Consolidar se mesmo número de NF + mesma data
- PAGAMENTOS: NÃO consolidar (podem haver múltiplos pagamentos no mesmo dia)
"""

from decimal import Decimal
from typing import List, Dict
from datetime import datetime


def consolidar_lancamentos_fornecedor(lancamentos: List[Dict]) -> List[Dict]:
    """
    Consolida lançamentos de COMPRA que têm o mesmo número de NF e mesma data.
    
    Regras:
    - Apenas lançamentos tipo "COMPRA" são consolidados
    - Lançamentos tipo "PAGAMENTO" permanecem separados
    - Consolidação: mesmo numero_nf + mesma data_lancamento
    - Valor consolidado: soma dos valores_credito
    
    Args:
        lancamentos: Lista de lançamentos extraídos pelo parser
        
    Returns:
        Lista de lançamentos consolidados
    """
    
    # Separar compras e pagamentos
    compras = [l for l in lancamentos if l.get('tipo_operacao') == 'COMPRA']
    outros = [l for l in lancamentos if l.get('tipo_operacao') != 'COMPRA']
    
    # Agrupar compras por NF + data
    grupos = {}
    
    for lanc in compras:
        nf = lanc.get('numero_nf')
        data = lanc.get('data_lancamento')
        
        # Chave: numero_nf + data (formato YYYY-MM-DD)
        if isinstance(data, datetime):
            data_str = data.strftime('%Y-%m-%d')
        else:
            data_str = str(data)
        
        # Compras sem NF não são consolidadas
        if not nf or nf == '':
            chave = f"SEM_NF_{id(lanc)}"  # ID único para não consolidar
        else:
            chave = f"{nf}_{data_str}"
        
        if chave not in grupos:
            grupos[chave] = []
        
        grupos[chave].append(lanc)
    
    # Consolidar grupos
    compras_consolidadas = []
    
    for chave, grupo in grupos.items():
        if len(grupo) == 1:
            # Apenas 1 lançamento, manter original
            compras_consolidadas.append(grupo[0])
        else:
            # Múltiplos lançamentos, consolidar
            primeiro = grupo[0]
            
            # Somar valores
            valor_total = sum(
                Decimal(str(l.get('valor_credito', 0))) 
                for l in grupo
            )
            
            # Criar lançamento consolidado
            consolidado = primeiro.copy()
            consolidado['valor_credito'] = valor_total
            
            # Concatenar históricos (opcional)
            historicos = [l.get('historico', '') for l in grupo]
            if len(set(historicos)) > 1:
                # Históricos diferentes, pegar o primeiro
                pass
            
            # Marcar como consolidado
            consolidado['consolidado'] = True
            consolidado['lancamentos_originais'] = len(grupo)
            
            compras_consolidadas.append(consolidado)
    
    # Juntar compras consolidadas + outros lançamentos
    resultado = compras_consolidadas + outros
    
    # Ordenar por data
    resultado.sort(key=lambda x: x.get('data_lancamento'))
    
    return resultado


def consolidar_todos_fornecedores(dados_parser: Dict) -> Dict:
    """
    Aplica consolidação em todos os fornecedores extraídos pelo parser.
    
    Args:
        dados_parser: Dict retornado por parsear_arquivo_razao()
        
    Returns:
        Dict com mesma estrutura, mas lançamentos consolidados
    """
    
    resultado = dados_parser.copy()
    
    print("🔧 Consolidando lançamentos...")
    
    for fornecedor in resultado['fornecedores']:
        # Consolidar lançamentos
        lancamentos_originais = fornecedor['lancamentos']
        lancamentos_consolidados = consolidar_lancamentos_fornecedor(lancamentos_originais)
        
        # Atualizar fornecedor
        fornecedor['lancamentos'] = lancamentos_consolidados
        
        # Recalcular totais (não mudam, mas por garantia)
        total_credito = sum(
            Decimal(str(l.get('valor_credito', 0))) 
            for l in lancamentos_consolidados 
            if l.get('tipo_operacao') == 'COMPRA'
        )
        
        total_debito = sum(
            Decimal(str(l.get('valor_debito', 0))) 
            for l in lancamentos_consolidados 
            if l.get('tipo_operacao') == 'PAGAMENTO'
        )
        
        fornecedor['total_credito'] = float(total_credito)
        fornecedor['total_debito'] = float(total_debito)
        
        # Informação de quantos foram consolidados
        qtd_original = len(lancamentos_originais)
        qtd_consolidado = len(lancamentos_consolidados)
        
        if qtd_consolidado < qtd_original:
            print(f"   ✅ {fornecedor['nome_fornecedor'][:40]}: "
                  f"{qtd_original} → {qtd_consolidado} lançamentos "
                  f"({qtd_original - qtd_consolidado} consolidados)")
    
    return resultado