const { ValidationError } = require('../middlewares/errorHandler');

function validateCheckout(body = {}) {
    const { usr: name, eml: email, pwd: password, c_id: courseId, card } = body;

    if (!name || !email || !courseId || !card) {
        throw new ValidationError('Bad Request');
    }
    if (typeof card !== 'string' || typeof email !== 'string') {
        throw new ValidationError('Bad Request');
    }

    return { name, email, password, courseId, card };
}

function validateUserId(rawId) {
    const id = Number(rawId);
    if (!Number.isInteger(id)) {
        throw new ValidationError('Bad Request');
    }
    return id;
}

module.exports = { validateCheckout, validateUserId };
