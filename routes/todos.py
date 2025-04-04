from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
from datetime import datetime
from models import db, Task
from utils import format_date, get_category_stats, get_status_stats, get_due_date_stats

todos = Blueprint('todos', __name__)

@todos.route('/')
@login_required
def home():
    # Get tasks for the current user
    tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.created_at.desc()).all()
    
    # Get task statistics
    category_stats = get_category_stats(tasks)
    status_stats = get_status_stats(tasks)
    due_date_stats = get_due_date_stats(tasks)
    
    return render_template('home.html', 
                           tasks=tasks, 
                           format_date=format_date,
                           category_stats=category_stats,
                           status_stats=status_stats,
                           due_date_stats=due_date_stats)

@todos.route('/task/new', methods=['POST'])
@login_required
def new_task():
    title = request.form.get('title')
    description = request.form.get('description')
    category = request.form.get('category')
    priority = request.form.get('priority')
    due_date_str = request.form.get('due_date')
    
    if not title:
        flash('Task title is required.', 'danger')
        return redirect(url_for('todos.home'))
    
    # Parse due date if provided
    due_date = None
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
        except ValueError:
            flash('Invalid date format.', 'danger')
            return redirect(url_for('todos.home'))
    
    # Create new task
    new_task = Task(
        title=title,
        description=description,
        category=category,
        priority=priority,
        due_date=due_date,
        user_id=current_user.id
    )
    
    db.session.add(new_task)
    db.session.commit()
    
    flash('Task created successfully!', 'success')
    return redirect(url_for('todos.home'))

@todos.route('/task/<int:task_id>/update', methods=['POST'])
@login_required
def update_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    
    title = request.form.get('title')
    description = request.form.get('description')
    category = request.form.get('category')
    priority = request.form.get('priority')
    status = request.form.get('status')
    due_date_str = request.form.get('due_date')
    
    if not title:
        flash('Task title is required.', 'danger')
        return redirect(url_for('todos.home'))
    
    # Update task fields
    task.title = title
    task.description = description
    task.category = category
    task.priority = priority
    task.status = status
    
    # Parse due date if provided
    if due_date_str:
        try:
            task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
        except ValueError:
            flash('Invalid date format.', 'danger')
            return redirect(url_for('todos.home'))
    else:
        task.due_date = None
    
    db.session.commit()
    
    flash('Task updated successfully!', 'success')
    return redirect(url_for('todos.home'))

@todos.route('/task/<int:task_id>/toggle', methods=['POST'])
@login_required
def toggle_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    
    # Toggle completion status
    task.completed = not task.completed
    
    # Update status if completed
    if task.completed:
        task.status = 'completed'
    else:
        task.status = 'pending'
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'completed': task.completed,
        'status': task.status
    })

@todos.route('/task/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    
    db.session.delete(task)
    db.session.commit()
    
    flash('Task deleted successfully!', 'success')
    return redirect(url_for('todos.home'))

@todos.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        # Update user settings
        dark_mode = True if request.form.get('dark_mode') else False
        
        current_user.dark_mode = dark_mode
        db.session.commit()
        
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('todos.settings'))
    
    return render_template('settings.html')