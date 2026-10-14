const express = require('express');

module.exports = (controller, adminAuth) => {
    const router = express.Router();
    router.get('/admin/financial-report', adminAuth, (req, res, next) =>
        controller.financialReport().then((report) => res.json(report)).catch(next));
    return router;
};
