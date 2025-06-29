from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from .models import db, User
from .rbac import role_required

main = Blueprint('main', __name__)

@main.route('/')
def home():
    return redirect(url_for('main.login'))

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            return redirect(url_for('main.dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

@main.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))

@main.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    if session['role'] == 'employee':
        return render_template('dashboard_employee.html')
    return render_template('dashboard.html')

@main.route('/users')
@role_required('super_admin')
def users():
    users = User.query.order_by(User.id.desc()).all()
    return render_template('users.html', users=users)

@main.route('/users/add', methods=['GET', 'POST'])
@role_required('super_admin')
def add_user():
    if request.method == 'POST':
        if User.query.filter_by(username=request.form['username']).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('main.add_user'))
        new_user = User(
            name=request.form['name'],
            username=request.form['username'],
            password=generate_password_hash(request.form['password']),
            role=request.form['role']
        )
        db.session.add(new_user)
        db.session.commit()
        flash('User created successfully.', 'success')
        return redirect(url_for('main.users'))
    return render_template('add_user.html')

@main.route('/users/promote/<int:user_id>')
@role_required('super_admin')
def promote_user(user_id):
    if 'user_id' not in session or session.get('role') != 'super_admin':
        flash('Access denied', 'danger')
        return redirect(url_for('main.dashboard'))

    user = User.query.get_or_404(user_id)
    if user.role == 'employee':
        user.role = 'admin'
        db.session.commit()
        flash(f'{user.username} promoted to Admin.', 'success')
    return redirect(url_for('main.users'))

@main.route('/users/demote/<int:user_id>')
@role_required('super_admin')
def demote_user(user_id):
    if 'user_id' not in session or session.get('role') != 'super_admin':
        flash('Access denied', 'danger')
        return redirect(url_for('main.dashboard'))

    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        user.role = 'employee'
        db.session.commit()
        flash(f'{user.username} demoted to Employee.', 'warning')
    return redirect(url_for('main.users'))

@main.route('/users/delete/<int:user_id>')
@role_required('super_admin')
def delete_user(user_id):
    if 'user_id' not in session or session.get('role') != 'super_admin':
        flash('Access denied', 'danger')
        return redirect(url_for('main.dashboard'))

    user = User.query.get_or_404(user_id)
    if user.role != 'super_admin':
        db.session.delete(user)
        db.session.commit()
        flash(f'{user.username} deleted.', 'danger')
    return redirect(url_for('main.users'))