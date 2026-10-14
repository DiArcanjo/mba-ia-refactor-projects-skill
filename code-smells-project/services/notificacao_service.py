import logging

logger = logging.getLogger(__name__)


def pedido_criado(pedido_id, usuario_id):
    logger.info("Email: pedido %s criado para usuario %s", pedido_id, usuario_id)
    logger.info("SMS: pedido %s recebido", pedido_id)
    logger.info("Push: novo pedido %s recebido pelo sistema", pedido_id)


def status_pedido_alterado(pedido_id, novo_status):
    logger.info("Pedido %s alterado para status %s", pedido_id, novo_status)
