const { PAYMENT_STATUS } = require('../config/constants');
const { NotFoundError, ValidationError } = require('../middlewares/errorHandler');
const { hashPassword, generateRandomPassword } = require('../services/passwordService');
const { validateCheckout } = require('./validators');

class CheckoutController {
    constructor({ db, userModel, courseModel, enrollmentModel, paymentModel, auditLogModel, paymentService }) {
        this.db = db;
        this.userModel = userModel;
        this.courseModel = courseModel;
        this.enrollmentModel = enrollmentModel;
        this.paymentModel = paymentModel;
        this.auditLogModel = auditLogModel;
        this.paymentService = paymentService;
    }

    async checkout(body) {
        const { name, email, password, courseId, card } = validateCheckout(body);

        const course = await this.courseModel.findActiveById(courseId);
        if (!course) throw new NotFoundError('Curso não encontrado');

        const status = this.paymentService.authorize(card);
        if (status === PAYMENT_STATUS.DENIED) throw new ValidationError('Pagamento recusado');

        return this.db.transaction(async () => {
            const existingUser = await this.userModel.findByEmail(email);
            const userId = existingUser
                ? existingUser.id
                : await this.userModel.create({
                    name,
                    email,
                    passwordHash: await hashPassword(password || generateRandomPassword()),
                });

            const enrollmentId = await this.enrollmentModel.create(userId, courseId);
            await this.paymentModel.create(enrollmentId, course.price, status);
            await this.auditLogModel.create(`Checkout curso ${courseId} por ${userId}`);

            return { msg: 'Sucesso', enrollment_id: enrollmentId };
        });
    }
}

module.exports = CheckoutController;
