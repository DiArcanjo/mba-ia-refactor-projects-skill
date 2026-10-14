module.exports = {
    port: Number(process.env.PORT) || 3000,
    databasePath: process.env.DATABASE_PATH || ':memory:',
    adminToken: process.env.ADMIN_TOKEN || '',
};
