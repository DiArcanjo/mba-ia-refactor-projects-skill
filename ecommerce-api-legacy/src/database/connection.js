const sqlite3 = require('sqlite3');

function createDatabase(path) {
    return new Promise((resolve, reject) => {
        const raw = new sqlite3.Database(path, (err) => {
            if (err) return reject(err);
            resolve(wrap(raw));
        });
    });
}

function wrap(raw) {
    const run = (sql, params = []) => new Promise((resolve, reject) => {
        raw.run(sql, params, function (err) {
            if (err) return reject(err);
            resolve({ lastID: this.lastID, changes: this.changes });
        });
    });
    const get = (sql, params = []) => new Promise((resolve, reject) =>
        raw.get(sql, params, (err, row) => (err ? reject(err) : resolve(row))));
    const all = (sql, params = []) => new Promise((resolve, reject) =>
        raw.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows))));

    let queue = Promise.resolve();
    const transaction = (work) => {
        const result = queue.then(async () => {
            await run('BEGIN');
            try {
                const value = await work();
                await run('COMMIT');
                return value;
            } catch (err) {
                await run('ROLLBACK');
                throw err;
            }
        });
        queue = result.catch(() => {});
        return result;
    };

    const close = () => new Promise((resolve, reject) =>
        raw.close((err) => (err ? reject(err) : resolve())));

    return { run, get, all, transaction, close };
}

module.exports = { createDatabase };
