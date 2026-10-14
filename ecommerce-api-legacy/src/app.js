const express = require('express');
const config = require('./config');
const { createDatabase } = require('./database/connection');
const { initSchema, seed } = require('./database/schema');
const UserModel = require('./models/userModel');
const CourseModel = require('./models/courseModel');
const EnrollmentModel = require('./models/enrollmentModel');
const PaymentModel = require('./models/paymentModel');
const AuditLogModel = require('./models/auditLogModel');
const PaymentService = require('./services/paymentService');
const CheckoutController = require('./controllers/checkoutController');
const ReportController = require('./controllers/reportController');
const UserController = require('./controllers/userController');
const checkoutRoutes = require('./routes/checkoutRoutes');
const reportRoutes = require('./routes/reportRoutes');
const userRoutes = require('./routes/userRoutes');
const adminAuth = require('./middlewares/adminAuth');
const { errorHandler } = require('./middlewares/errorHandler');

async function createApp() {
    const db = await createDatabase(config.databasePath);
    await initSchema(db);
    await seed(db);

    const userModel = new UserModel(db);
    const courseModel = new CourseModel(db);
    const enrollmentModel = new EnrollmentModel(db);
    const paymentModel = new PaymentModel(db);
    const auditLogModel = new AuditLogModel(db);

    const checkoutController = new CheckoutController({
        db,
        userModel,
        courseModel,
        enrollmentModel,
        paymentModel,
        auditLogModel,
        paymentService: new PaymentService(),
    });
    const reportController = new ReportController({ enrollmentModel });
    const userController = new UserController({ userModel });
    const requireAdmin = adminAuth(config.adminToken);

    const app = express();
    app.use(express.json());
    app.use('/api', checkoutRoutes(checkoutController));
    app.use('/api', reportRoutes(reportController, requireAdmin));
    app.use('/api', userRoutes(userController, requireAdmin));
    app.use(errorHandler);

    return app;
}

createApp()
    .then((app) => app.listen(config.port, () => {
        console.log(`Frankenstein LMS rodando na porta ${config.port}...`);
    }))
    .catch((err) => {
        console.error(err);
        process.exit(1);
    });
