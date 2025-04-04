from datetime import datetime, timedelta
from flask import session
from functools import wraps
from flask import redirect, url_for
from flask_login import current_user

def format_date(date_obj):
    """Format a datetime object to a readable string"""
    if not date_obj:
        return ""
    
    # Format: "Mon, 22 Apr 2025"
    return date_obj.strftime("%a, %d %b %Y")

def get_category_stats(tasks):
    """Get statistics about task categories"""
    categories = {
        'work': 0,
        'personal': 0,
        'shopping': 0,
        'health': 0,
        'finance': 0,
        'other': 0
    }
    
    for task in tasks:
        if task.category in categories:
            categories[task.category] += 1
        else:
            categories['other'] += 1
    
    return categories

def get_status_stats(tasks):
    """Get statistics about task statuses"""
    statuses = {
        'pending': 0,
        'in-progress': 0,
        'completed': 0
    }
    
    for task in tasks:
        if task.status in statuses:
            statuses[task.status] += 1
    
    return statuses

def get_due_date_stats(tasks):
    """Get statistics about upcoming due dates"""
    today = datetime.utcnow().date()
    
    stats = {
        'overdue': 0,
        'today': 0,
        'tomorrow': 0,
        'this_week': 0,
        'later': 0,
        'no_date': 0
    }
    
    for task in tasks:
        if not task.due_date:
            stats['no_date'] += 1
            continue
        
        due_date = task.due_date.date()
        
        if due_date < today:
            stats['overdue'] += 1
        elif due_date == today:
            stats['today'] += 1
        elif due_date == today + timedelta(days=1):
            stats['tomorrow'] += 1
        elif due_date <= today + timedelta(days=7):
            stats['this_week'] += 1
        else:
            stats['later'] += 1
    
    return stats

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function