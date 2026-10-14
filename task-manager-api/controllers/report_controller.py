from datetime import timedelta

from config.settings import (
    HIGH_PRIORITY_THRESHOLD,
    PRIORITY_LABELS,
    RECENT_ACTIVITY_DAYS,
    STATUS_DONE,
    TASK_STATUSES,
)
from database.connection import utcnow
from middlewares.error_handler import NotFoundError
from models.category import Category
from models.task import Task
from models.user import User


def _completion_rate(done, total):
    return round((done / total) * 100, 2) if total > 0 else 0


def summary_report():
    now = utcnow()
    since = now - timedelta(days=RECENT_ACTIVITY_DAYS)
    status_counts = Task.count_by_status()
    priority_counts = Task.count_by_priority()
    totals_by_user = Task.totals_by_user()
    overdue_tasks = Task.find_overdue()

    user_stats = []
    for user in User.list_all():
        total, completed = totals_by_user.get(user.id, (0, 0))
        user_stats.append({
            'user_id': user.id,
            'user_name': user.name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': _completion_rate(completed, total),
        })

    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': sum(status_counts.values()),
            'total_users': User.count(),
            'total_categories': Category.count(),
        },
        'tasks_by_status': {status: status_counts.get(status, 0) for status in TASK_STATUSES},
        'tasks_by_priority': {
            label: priority_counts.get(priority, 0) for priority, label in PRIORITY_LABELS.items()
        },
        'overdue': {
            'count': len(overdue_tasks),
            'tasks': [
                {
                    'id': task.id,
                    'title': task.title,
                    'due_date': str(task.due_date),
                    'days_overdue': (now - task.due_date).days,
                }
                for task in overdue_tasks
            ],
        },
        'recent_activity': {
            'tasks_created_last_7_days': Task.count_created_since(since),
            'tasks_completed_last_7_days': Task.count_done_since(since),
        },
        'user_productivity': user_stats,
    }


def user_report(user_id):
    user = User.find(user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')

    status_counts = Task.count_by_status(user_id)
    priority_counts = Task.count_by_priority(user_id)
    total = sum(status_counts.values())
    done = status_counts.get(STATUS_DONE, 0)
    high_priority = sum(
        count for priority, count in priority_counts.items()
        if priority is not None and priority <= HIGH_PRIORITY_THRESHOLD
    )

    return {
        'user': {'id': user.id, 'name': user.name, 'email': user.email},
        'statistics': {
            'total_tasks': total,
            **{status: status_counts.get(status, 0) for status in TASK_STATUSES},
            'overdue': len(Task.find_overdue(user_id)),
            'high_priority': high_priority,
            'completion_rate': _completion_rate(done, total),
        },
    }
