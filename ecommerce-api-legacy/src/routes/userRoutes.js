const express = require('express');

module.exports = (controller, adminAuth) => {
    const router = express.Router();
    router.delete('/users/:id', adminAuth, (req, res, next) =>
        controller.remove(req.params.id).then((message) => res.send(message)).catch(next));
    return router;
};
