const { PAYMENT_STATUS, APPROVED_CARD_PREFIX } = require('../config/constants');

class PaymentService {
    authorize(card) {
        return card.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
    }
}

module.exports = PaymentService;
