def _format_date(value):
    return str(value) if value else None


def serialize_task(task):
    return {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'priority': task.priority,
        'user_id': task.user_id,
        'category_id': task.category_id,
        'created_at': str(task.created_at),
        'updated_at': str(task.updated_at),
        'due_date': _format_date(task.due_date),
        'tags': task.tags.split(',') if task.tags else [],
    }


def serialize_task_with_overdue(task):
    return {**serialize_task(task), 'overdue': task.is_overdue()}


def serialize_task_listing(task):
    return {
        **serialize_task_with_overdue(task),
        'user_name': task.user.name if task.user else None,
        'category_name': task.category.name if task.category else None,
    }


def serialize_user_task(task):
    return {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'priority': task.priority,
        'created_at': str(task.created_at),
        'due_date': _format_date(task.due_date),
        'overdue': task.is_overdue(),
    }


def serialize_user(user):
    return {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'role': user.role,
        'active': user.active,
        'created_at': str(user.created_at),
    }


def serialize_user_with_task_count(user, task_count):
    return {**serialize_user(user), 'task_count': task_count}


def serialize_category(category):
    return {
        'id': category.id,
        'name': category.name,
        'description': category.description,
        'color': category.color,
        'created_at': str(category.created_at),
    }


def serialize_category_with_task_count(category, task_count):
    return {**serialize_category(category), 'task_count': task_count}
