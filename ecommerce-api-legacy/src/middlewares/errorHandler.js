class AppError extends Error {
    constructor(message, status) {
        super(message);
        this.status = status;
    }
}

class ValidationError extends AppError {
    constructor(message) {
        super(message, 400);
    }
}

class NotFoundError extends AppError {
    constructor(message) {
        super(message, 404);
    }
}

class UnauthorizedError extends AppError {
    constructor(message) {
        super(message, 401);
    }
}

function errorHandler(err, req, res, next) {
    const status = err.status || 500;
    if (status >= 500) {
        console.error(err);
        return res.status(500).send('Erro interno');
    }
    res.status(status).send(err.message);
}

module.exports = { AppError, ValidationError, NotFoundError, UnauthorizedError, errorHandler };
