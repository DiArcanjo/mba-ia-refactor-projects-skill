const { SEED_USER_PASSWORD } = require('../config/constants');
const { hashPassword } = require('../services/passwordService');

async function initSchema(db) {
    await db.run('PRAGMA foreign_keys = ON');
    await db.run('CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)');
    await db.run('CREATE TABLE courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)');
    await db.run(`CREATE TABLE enrollments (
        id INTEGER PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        course_id INTEGER REFERENCES courses(id)
    )`);
    await db.run(`CREATE TABLE payments (
        id INTEGER PRIMARY KEY,
        enrollment_id INTEGER REFERENCES enrollments(id) ON DELETE CASCADE,
        amount REAL,
        status TEXT
    )`);
    await db.run('CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)');
}

async function seed(db) {
    const passwordHash = await hashPassword(SEED_USER_PASSWORD);
    await db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', ['Leonan', 'leonan@fullcycle.com.br', passwordHash]);
    await db.run("INSERT INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1), ('Docker', 497.00, 1)");
    await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
    await db.run("INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, 'PAID')");
}

module.exports = { initSchema, seed };
