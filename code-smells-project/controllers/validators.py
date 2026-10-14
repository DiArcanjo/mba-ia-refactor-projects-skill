from config.settings import CATEGORIAS_VALIDAS, CATEGORIA_PADRAO, NOME_PRODUTO_MAX, NOME_PRODUTO_MIN
from middlewares.error_handler import ValidationError


def exigir_dados(dados):
    if not dados or not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")
    return dados


def _numero(valor, mensagem):
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ValidationError(mensagem)
    return valor


def validar_produto(dados, validar_nome_e_categoria):
    if "nome" not in dados:
        raise ValidationError("Nome é obrigatório")
    if "preco" not in dados:
        raise ValidationError("Preço é obrigatório")
    if "estoque" not in dados:
        raise ValidationError("Estoque é obrigatório")

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    categoria = dados.get("categoria", CATEGORIA_PADRAO)
    if not isinstance(nome, str) or not isinstance(descricao, str) or not isinstance(categoria, str):
        raise ValidationError("Nome, descrição e categoria devem ser texto")
    preco = _numero(dados["preco"], "Preço deve ser numérico")
    estoque = _numero(dados["estoque"], "Estoque deve ser numérico")

    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if validar_nome_e_categoria:
        if len(nome) < NOME_PRODUTO_MIN:
            raise ValidationError("Nome muito curto")
        if len(nome) > NOME_PRODUTO_MAX:
            raise ValidationError("Nome muito longo")
        if categoria not in CATEGORIAS_VALIDAS:
            raise ValidationError("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS))

    return {"nome": nome, "descricao": descricao, "preco": preco, "estoque": estoque, "categoria": categoria}


def validar_itens_pedido(itens):
    if not itens or not isinstance(itens, list):
        raise ValidationError("Pedido deve ter pelo menos 1 item")
    for item in itens:
        if not isinstance(item, dict):
            raise ValidationError("Item de pedido inválido")
        produto_id, quantidade = item.get("produto_id"), item.get("quantidade")
        if not isinstance(produto_id, int) or not isinstance(quantidade, int) or isinstance(quantidade, bool):
            raise ValidationError("Item de pedido inválido")
        if quantidade <= 0:
            raise ValidationError("Quantidade deve ser maior que zero")
    return itens
