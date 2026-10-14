const express = require('express');

module.exports = (controller) => {
    const router = express.Router();
    router.post('/checkout', (req, res, next) =>
        controller.checkout(req.body).then((result) => res.status(200).json(result)).catch(next));
    return router;
};
