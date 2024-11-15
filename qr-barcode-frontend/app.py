from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from models import db, User, Item
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'QRBARCODE_KEY'

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///qr_barcode.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db.init_app(app)

# Ensure all tables exist
with app.app_context():
    db.create_all()

# Login and user management routes
@app.route('/')
def home():
    session.clear()
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Clear any existing flash messages when accessing login page
    if request.method == 'GET':
        session.pop('_flashes', None)
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            return jsonify({
                'message': 'Login successful!',
                'redirect': url_for('engineering_interface')
            }), 200
        else:
            return jsonify({
                'error': 'Invalid username or password'
            }), 401

    return render_template('login.html')

@app.route('/logout', methods=['POST'])
def logout():
    return redirect(url_for('login'))

# User management routes
@app.route('/manage-accounts')
def manage_accounts():
    users = User.query.all()
    return render_template('manage_accounts.html', users=users)

@app.route('/create-account', methods=['POST'])
def create_account():
    if request.method == 'POST':
        try:
            new_user = User(
                first_name=request.form['first_name'],
                middle_name=request.form['middle_name'],
                surname=request.form['surname'],
                section=request.form['section'],
                username=request.form['username'],
                role=request.form['role'],
                password=generate_password_hash(request.form['password'])
            )
            
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully!', 'success')
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating account: {str(e)}")
            flash('Error creating account. Please try again.', 'error')
            
    return redirect(url_for('manage_accounts'))

@app.route('/edit-user/<int:user_id>')
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('edit_user.html', user=user)

@app.route('/update-user/<int:user_id>', methods=['POST'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    
    try:
        user.first_name = request.form['first_name']
        user.middle_name = request.form['middle_name']
        user.surname = request.form['surname']
        user.section = request.form['section']
        user.username = request.form['username']
        user.role = request.form['role']
        
        if request.form['password']:
            user.password = generate_password_hash(request.form['password'])
        
        db.session.commit()
        flash('Account updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"Error updating account: {str(e)}")
        flash('Error updating account. Please try again.', 'error')
    
    return redirect(url_for('manage_accounts'))

@app.route('/delete-users', methods=['POST'])
def delete_users():
    user_ids = request.form.getlist('user_ids[]')
    for user_id in user_ids:
        user = User.query.get(user_id)
        if user:
            db.session.delete(user)
    db.session.commit()
    return redirect(url_for('manage_existing_accounts'))

# Item management routes
@app.route('/item-masterlist')
def item_masterlist():
    items = Item.query.all()
    return render_template('item_masterlist.html', items=items)

@app.route('/register-item')
def register_item():
    return render_template('register_item.html')

@app.route('/revise-item/<int:item_id>')
def revise_item_page(item_id):
    item = Item.query.get_or_404(item_id)
    return render_template('revise_item.html', item=item)

@app.route('/delete-items', methods=['POST'])
def delete_items():
    if request.method == 'POST':
        item_ids = request.form.getlist('item_ids[]')
        try:
            for item_id in item_ids:
                item = Item.query.get(item_id)
                if item:
                    db.session.delete(item)
            db.session.commit()
            flash('Items deleted successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting items: {str(e)}")
            flash('Error deleting items. Please try again.', 'error')
    
    return redirect(url_for('item_masterlist'))

@app.route('/create-item', methods=['POST'])
def create_item():
    try:
        # Get item data from session
        item_data = session.get('item_data', {})
        
        # Get sublot configuration
        enable_sublot = request.form.get('enable_sublot') == 'on'
        serial_numbers = request.form.get('serial_numbers', '')
        
        # Create new item
        new_item = Item(
            name=item_data['name'],
            revision=item_data['revision'],
            code_count=item_data['code_count'],
            category=item_data['category'],
            label_content=item_data['label_content'],
            qr_content=f"{item_data['label_content']}-{item_data['revision']}"
        )
        
        db.session.add(new_item)
        db.session.commit()
        
        # Clear the session data
        session.pop('item_data', None)
        
        flash('Item registered successfully!', 'success')
        return redirect(url_for('item_masterlist'))
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating item: {str(e)}")
        flash('Error registering item. Please try again.', 'error')
        return redirect(url_for('register_item'))

@app.route('/update-item/<int:item_id>', methods=['POST'])
def update_item(item_id):
    item = Item.query.get_or_404(item_id)
    try:
        item.name = request.form['name']
        item.revision = int(request.form['revision'])
        item.code_count = int(request.form['code_count'])
        item.category = request.form['category']
        item.label_content = request.form['label_content']
        item.qr_content = f"{request.form['label_content']}-{request.form['revision']}"
        item.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Item updated successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating item: {str(e)}")
        flash('Error updating item. Please try again.', 'error')
        
    return redirect(url_for('item_masterlist'))

@app.route('/sublot_config/<int:item_id>')
def sublot_config(item_id):
    return render_template('sublot_config.html', item_id=item_id)

@app.route('/revise_item/<int:item_id>', methods=['POST'])
def revise_item(item_id):
    # Get form data
    enable_sublot = request.form.get('enable_sublot') == 'on'
    serial_numbers = request.form.get('serial_numbers')
    
    # Get the item
    item = Item.query.get_or_404(item_id)
    
    # Store the data in session for later use
    session['sublot_config'] = {
        'enable_sublot': enable_sublot,
        'serial_numbers': serial_numbers
    }
    
    # Render the review page
    return render_template('review_item.html', 
                         item_id=item_id,
                         enable_sublot=enable_sublot,
                         serial_numbers=serial_numbers)

# Add this route after the login route
@app.route('/engineering')
def engineering_interface():
    return render_template('engineer_login.html')

# Add this route for account settings
@app.route('/account-settings')
def account_settings():
    users = User.query.all()
    return render_template('account_settings.html', users=users)

@app.route('/new-account')
def new_account():
    return render_template('new_account.html')

if __name__ == '__main__':
    app.run(debug=True)
