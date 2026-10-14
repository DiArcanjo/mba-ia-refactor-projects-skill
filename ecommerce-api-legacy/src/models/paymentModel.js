class PaymentModel {
    constructor(db) {
        this.db = db;
    }

    create(enrollmentId, amount, status) {
        return this.db.run(
            'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
            [enrollmentId, amount, status],
        );
    }
}

module.exports = PaymentModel;
