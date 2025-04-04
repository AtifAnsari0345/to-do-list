from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_pymongo import PyMongo
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from bson.objectid import ObjectId
import os
from datetime import datetime, timedelta
import json
from config import Config

# Initialize Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Initialize MongoDB
mongo = PyMongo(app)

# Initialize Bcrypt for password hashing
bcrypt = Bcrypt(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User model for Flask-Login
class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.email = user_data['email']
        self.theme = user_data.get('theme', 'light')
        self.notification_pref = user_data.get('notification_pref', True)

    @staticmethod
    def get(user_id):
        user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        if user_data:
            return User(user_data)
        return None

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = mongo.db.users.find_one({'username': username})
        
        if user and bcrypt.check_password_hash(user['password'], password):
            login_user(User(user))
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Login failed. Please check your username and password.', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template('register.html')
        
        # Check if username or email already exists
        if mongo.db.users.find_one({'$or': [{'username': username}, {'email': email}]}):
            flash('Username or email already exists. Please choose another one.', 'danger')
            return render_template('register.html')
        
        # Hash password and create user
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user_data = {
            'username': username,
            'email': email,
            'password': hashed_password,
            'created_at': datetime.now(),
            'theme': 'light',
            'notification_pref': True
        }
        
        mongo.db.users.insert_one(user_data)
        flash('Registration successful! You can now login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    todos = list(mongo.db.todos.find({'user_id': current_user.id}).sort('due_date', 1))
    
    # Format dates for display
    for todo in todos:
        if 'due_date' in todo and todo['due_date']:
            todo['due_date_formatted'] = todo['due_date'].strftime('%Y-%m-%d %H:%M')
        else:
            todo['due_date_formatted'] = None
    
    return render_template('home.html', 
                          now=datetime.now(),
                          todos=todos, 
                          priorities=['Low', 'Medium', 'High', 'Urgent'],
                          categories=['Work', 'Personal', 'Shopping', 'Health', 'Finance', 'Other'])

@app.route('/add_todo', methods=['POST'])
@login_required
def add_todo():
    title = request.form.get('title')
    description = request.form.get('description', '')
    priority = request.form.get('priority', 'Medium')
    category = request.form.get('category', 'Other')
    due_date_str = request.form.get('due_date', '')
    
    due_date = None
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Invalid date format', 'danger')
            return redirect(url_for('dashboard'))
    
    todo = {
        'user_id': current_user.id,
        'title': title,
        'description': description,
        'priority': priority,
        'category': category,
        'due_date': due_date,
        'completed': False,
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }
    
    mongo.db.todos.insert_one(todo)
    flash('Task added successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/update_todo/<todo_id>', methods=['POST'])
@login_required
def update_todo(todo_id):
    todo = mongo.db.todos.find_one({'_id': ObjectId(todo_id)})
    
    # Check if todo exists and belongs to current user
    if not todo or todo['user_id'] != current_user.id:
        flash('Task not found or access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    title = request.form.get('title')
    description = request.form.get('description', '')
    priority = request.form.get('priority', 'Medium')
    category = request.form.get('category', 'Other')
    due_date_str = request.form.get('due_date', '')
    
    due_date = None
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Invalid date format', 'danger')
            return redirect(url_for('dashboard'))
    
    mongo.db.todos.update_one(
        {'_id': ObjectId(todo_id)},
        {'$set': {
            'title': title,
            'description': description,
            'priority': priority,
            'category': category,
            'due_date': due_date,
            'updated_at': datetime.now()
        }}
    )
    
    flash('Task updated successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/toggle_todo/<todo_id>', methods=['POST'])
@login_required
def toggle_todo(todo_id):
    todo = mongo.db.todos.find_one({'_id': ObjectId(todo_id)})
    
    # Check if todo exists and belongs to current user
    if not todo or todo['user_id'] != current_user.id:
        return jsonify({'success': False, 'message': 'Task not found or access denied'})
    
    new_status = not todo['completed']
    
    mongo.db.todos.update_one(
        {'_id': ObjectId(todo_id)},
        {'$set': {
            'completed': new_status,
            'updated_at': datetime.now(),
            'completed_at': datetime.now() if new_status else None
        }}
    )
    
    return jsonify({'success': True, 'completed': new_status})

@app.route('/delete_todo/<todo_id>', methods=['POST'])
@login_required
def delete_todo(todo_id):
    todo = mongo.db.todos.find_one({'_id': ObjectId(todo_id)})
    
    # Check if todo exists and belongs to current user
    if not todo or todo['user_id'] != current_user.id:
        flash('Task not found or access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    mongo.db.todos.delete_one({'_id': ObjectId(todo_id)})
    flash('Task deleted successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        theme = request.form.get('theme', 'light')
        notification_pref = 'notification_pref' in request.form
        
        mongo.db.users.update_one(
            {'_id': ObjectId(current_user.id)},
            {'$set': {
                'theme': theme,
                'notification_pref': notification_pref
            }}
        )
        
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('settings'))
    
    user_data = mongo.db.users.find_one({'_id': ObjectId(current_user.id)})
    return render_template('settings.html', user=user_data)

@app.route('/api/upcoming_todos')
@login_required
def api_upcoming_todos():
    # Get todos due in the next 24 hours
    tomorrow = datetime.now() + timedelta(days=1)
    
    upcoming_todos = list(mongo.db.todos.find({
        'user_id': current_user.id,
        'completed': False,
        'due_date': {'$gte': datetime.now(), '$lte': tomorrow}
    }).sort('due_date', 1))
    
    # Convert ObjectId to string for JSON serialization
    for todo in upcoming_todos:
        todo['_id'] = str(todo['_id'])
        if 'due_date' in todo and todo['due_date']:
            todo['due_date'] = todo['due_date'].strftime('%Y-%m-%d %H:%M')
        if 'created_at' in todo:
            todo['created_at'] = todo['created_at'].strftime('%Y-%m-%d %H:%M')
        if 'updated_at' in todo:
            todo['updated_at'] = todo['updated_at'].strftime('%Y-%m-%d %H:%M')
        if 'completed_at' in todo and todo['completed_at']:
            todo['completed_at'] = todo['completed_at'].strftime('%Y-%m-%d %H:%M')
    
    return jsonify(upcoming_todos)

@app.route('/api/todo_stats')
@login_required
def api_todo_stats():
    total = mongo.db.todos.count_documents({'user_id': current_user.id})
    completed = mongo.db.todos.count_documents({'user_id': current_user.id, 'completed': True})
    pending = total - completed
    
    # Count by priority
    priority_stats = {}
    for priority in ['Low', 'Medium', 'High', 'Urgent']:
        count = mongo.db.todos.count_documents({
            'user_id': current_user.id, 
            'priority': priority,
            'completed': False
        })
        priority_stats[priority] = count
    
    # Count by category
    category_stats = {}
    for category in ['Work', 'Personal', 'Shopping', 'Health', 'Finance', 'Other']:
        count = mongo.db.todos.count_documents({
            'user_id': current_user.id, 
            'category': category
        })
        category_stats[category] = count
    
    return jsonify({
        'total': total,
        'completed': completed,
        'pending': pending,
        'completion_rate': (completed / total * 100) if total > 0 else 0,
        'by_priority': priority_stats,
        'by_category': category_stats
    })

@app.template_filter('priority_color')
def priority_color(priority):
    colors = {
        'Low': 'success',
        'Medium': 'info',
        'High': 'warning',
        'Urgent': 'danger'
    }
    return colors.get(priority, 'secondary')

@app.template_filter('format_date')
def format_date(date):
    if not date:
        return "No date"
    return date.strftime("%b %d, %Y at %H:%M")

if __name__ == '__main__':
    # Make sure the collections exist
    if 'users' not in mongo.db.list_collection_names():
        mongo.db.create_collection('users')
        
    if 'todos' not in mongo.db.list_collection_names():
        mongo.db.create_collection('todos')
        
    app.run(debug=True)