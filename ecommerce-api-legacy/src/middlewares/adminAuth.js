const { UnauthorizedError } = require('./errorHandler');

module.exports = (adminToken) => (req, res, next) => {
    if (!adminToken || req.get('X-Admin-Token') !== adminToken) {
        return next(new UnauthorizedError('Acesso restrito a administradores'));
    }
    next();
};
