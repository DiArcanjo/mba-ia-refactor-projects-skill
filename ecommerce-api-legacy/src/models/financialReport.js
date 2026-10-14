const { PAYMENT_STATUS, UNKNOWN_STUDENT } = require('../config/constants');

function buildFinancialReport(rows) {
    const coursesById = new Map();

    for (const row of rows) {
        if (!coursesById.has(row.course_id)) {
            coursesById.set(row.course_id, { course: row.course_title, revenue: 0, students: [] });
        }
        if (row.enrollment_id === null) continue;

        const courseData = coursesById.get(row.course_id);
        if (row.payment_status === PAYMENT_STATUS.PAID) {
            courseData.revenue += row.payment_amount;
        }
        courseData.students.push({
            student: row.student_name || UNKNOWN_STUDENT,
            paid: row.payment_amount || 0,
        });
    }

    return [...coursesById.values()];
}

module.exports = { buildFinancialReport };
