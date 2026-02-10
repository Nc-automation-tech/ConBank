"""
ConciliaÃ§Ã£o FIFO FLEXÃVEL - Aceita adiantamentos e pagamentos excedentes
Regras:
- Pagamentos podem ocorrer ANTES de compras (adiantamentos)
- Pagamentos excedentes geram "crÃ©dito do cliente" (saldo devedor do fornecedor)
- FIFO puro Ã© aplicado nas NFs existentes
- Adiantamentos sÃ£o contabilizados separadamente
"""

from decimal import Decimal
from typing import List, Dict
from collections import deque
from sqlalchemy.orm import Session
from models import Fornecedor, LancamentoFornecedor


# TolerÃ¢ncia para "zerar" centavos residuais por arredondamento
EPS = Decimal("0.01")


def _d(x) -> Decimal:
    return x if isinstance(x, Decimal) else Decimal(str(x or "0"))


def _is_open(compra: LancamentoFornecedor) -> bool:
    return _d(compra.valor_saldo) > EPS


def conciliar_fornecedor_inteligente(db: Session, fornecedor_id: int) -> int:
    """
    Concilia um fornecedor aplicando TODOS os pagamentos via FIFO flexÃ­vel.
    
    MUDANÃ‡A: Aceita pagamentos excedentes (adiantamentos) sem quebrar.
    
    COMPRA (crÃ©dito): cria/representa uma NF (imutÃ¡vel no valor_credito)
    PAGAMENTO (dÃ©bito): aplicado em cascata nas NFs mais antigas abertas
    ADIANTAMENTO: pagamento que nÃ£o encontra NF = crÃ©dito do cliente
    
    SaÃ­das:
    - Atualiza em cada COMPRA:
        valor_pago_parcial, valor_saldo, status_pagamento
    - Retorna quantidade de NFs ainda pendentes (abertas)
    """

    # Compras (NFs) e pagamentos, ambos em ordem de data
    compras = db.query(LancamentoFornecedor).filter(
        LancamentoFornecedor.fornecedor_id == fornecedor_id,
        LancamentoFornecedor.tipo_operacao == "COMPRA"
    ).order_by(LancamentoFornecedor.data_lancamento).all()

    pagamentos = db.query(LancamentoFornecedor).filter(
        LancamentoFornecedor.fornecedor_id == fornecedor_id,
        LancamentoFornecedor.tipo_operacao == "PAGAMENTO"
    ).order_by(LancamentoFornecedor.data_lancamento).all()

    if not compras:
        print(f"   âš ï¸ Nenhuma COMPRA encontrada; apenas pagamentos (adiantamentos)")
        return 0

    # Inicializa estado das compras (NF)
    for compra in compras:
        compra.valor_pago_parcial = Decimal("0")
        compra.valor_saldo = _d(compra.valor_credito)
        compra.status_pagamento = "PENDENTE"

    print(f"   ðŸ“‹ {len(compras)} NFs (COMPRA) encontradas")
    print(f"   ðŸ’³ {len(pagamentos)} pagamentos (PAGAMENTO) encontrados")

    # Monta "event stream" (crÃ©dito + dÃ©bito) em ordem temporal real
    # Importante: se houver mesma data, processa COMPRA antes de PAGAMENTO
    events = []
    for c in compras:
        events.append((c.data_lancamento, 0, c))  # 0 = compra primeiro
    for p in pagamentos:
        events.append((p.data_lancamento, 1, p))  # 1 = pagamento depois

    events.sort(key=lambda t: (t[0], t[1]))

    # Fila FIFO das NFs abertas
    fila = deque()
    
    # Controle de adiantamentos
    adiantamento_total = Decimal("0")

    # Processa eventos
    for _, tipo, obj in events:
        if tipo == 0:
            # COMPRA: entra na fila como NF aberta
            # Se houver adiantamento acumulado, aplica primeiro
            if adiantamento_total > 0 and _d(obj.valor_saldo) > 0:
                abate = min(adiantamento_total, _d(obj.valor_saldo))
                obj.valor_pago_parcial = abate
                obj.valor_saldo = _d(obj.valor_credito) - abate
                adiantamento_total -= abate
                
                if _d(obj.valor_saldo) <= EPS:
                    obj.valor_saldo = Decimal("0")
                    obj.status_pagamento = "PAGO"
                else:
                    obj.status_pagamento = "PARCIAL"
                    fila.append(obj)
                
                print(f"   ðŸ’° Adiantamento aplicado: R$ {abate:,.2f} na NF {obj.numero_nf or 'S/N'}")
            else:
                # Sem adiantamento, entra na fila normalmente
                if _d(obj.valor_saldo) > EPS:
                    fila.append(obj)
            continue

        # PAGAMENTO: aplica em cascata nas NFs abertas
        valor_pagamento = _d(obj.valor_debito)
        if valor_pagamento <= 0:
            continue

        restante = valor_pagamento

        # Garante que o topo da fila esteja realmente aberto (limpeza defensiva)
        while fila and not _is_open(fila[0]):
            fila.popleft()

        while restante > 0:
            if not fila:
                # MUDANÃ‡A: Ao invÃ©s de lanÃ§ar erro, acumula como adiantamento
                adiantamento_total += restante
                print(f"   âš¡ Adiantamento: R$ {restante:,.2f} (data={obj.data_lancamento.strftime('%Y-%m-%d')})")
                restante = Decimal("0")
                break

            nf_atual = fila[0]
            falta = _d(nf_atual.valor_saldo)

            abate = falta if falta < restante else restante

            # aplica abatimento
            nf_atual.valor_pago_parcial = _d(nf_atual.valor_pago_parcial) + abate
            nf_atual.valor_saldo = _d(nf_atual.valor_credito) - _d(nf_atual.valor_pago_parcial)

            # atualiza status
            if _d(nf_atual.valor_saldo) <= EPS:
                nf_atual.valor_saldo = Decimal("0")
                nf_atual.status_pagamento = "PAGO"
                fila.popleft()  # quitada sai da fila
            else:
                nf_atual.status_pagamento = "PARCIAL"

            restante -= abate

    db.commit()

    # Conta pendentes (NFs ainda abertas)
    pendentes = [c for c in compras if _d(c.valor_saldo) > EPS]
    parciais = [c for c in compras if c.status_pagamento == "PARCIAL"]
    
    if adiantamento_total > 0:
        print(f"   ðŸ’° Adiantamento total acumulado: R$ {adiantamento_total:,.2f}")
        print(f"   â„¹ï¸  Fornecedor tem CRÃ‰DITO (empresa pagou a mais)")
    
    print(f"   ✅ {len(pendentes)} NFs com saldo pendente | {len(parciais)} NFs parciais")

    return len(pendentes), len(parciais)


def conciliar_todos_fornecedores_inteligente(db: Session, arquivo_id: int):
    """
    Concilia todos os fornecedores de um arquivo usando FIFO flexÃ­vel.
    """
    fornecedores = db.query(Fornecedor).filter(
        Fornecedor.arquivo_origem_id == arquivo_id
    ).all()

    print(f"\nðŸ”„ Iniciando conciliaÃ§Ã£o FIFO flexÃ­vel para {len(fornecedores)} fornecedores...")

    for forn in fornecedores:
        if _d(forn.total_credito) > 0 or _d(forn.total_debito) > 0:
            print(f"\nðŸ”Œ {forn.codigo_conta} - {forn.nome_fornecedor[:40]}")
            try:
                pendentes, parciais = conciliar_fornecedor_inteligente(db, forn.id)
                forn.qtd_nfs_pendentes = pendentes
                forn.qtd_nfs_parciais = parciais
            except Exception as e:
                print(f"   âŒ Erro: {e}")
                import traceback
                traceback.print_exc()

    db.commit()
    print("\nâœ… ConciliaÃ§Ã£o FIFO flexÃ­vel concluÃ­da!")