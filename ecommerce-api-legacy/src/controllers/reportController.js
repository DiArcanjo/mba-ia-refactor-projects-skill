const { buildFinancialReport } = require('../models/financialReport');

class ReportController {
    constructor({ enrollmentModel }) {
        this.enrollmentModel = enrollmentModel;
    }

    async financialReport() {
        const rows = await this.enrollmentModel.findReportRows();
        return buildFinancialReport(rows);
    }
}

module.exports = ReportController;
