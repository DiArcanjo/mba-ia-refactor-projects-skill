from models import pedido_model


def relatorio_vendas(db):
    resumo = pedido_model.resumo_vendas(db)
    faturamento = resumo["faturamento"]
    total_pedidos = resumo["total_pedidos"]
    desconto = pedido_model.calcular_desconto(faturamento)
    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": resumo["pendentes"],
        "pedidos_aprovados": resumo["aprovados"],
        "pedidos_cancelados": resumo["cancelados"],
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }
