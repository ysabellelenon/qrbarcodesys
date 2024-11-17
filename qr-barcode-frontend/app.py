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
@app.route('/item-masterlist', methods=['GET', 'POST'])
def item_masterlist():
    if request.method == 'POST':
        try:
            # Get the item data from session if it exists
            item_data = session.get('item_data', {})
            
            # Clear the session data
            session.pop('item_data', None)
            
            flash('Item registered successfully!', 'success')
            return redirect(url_for('item_masterlist'))
            
        except Exception as e:
            print(f"Error registering item: {str(e)}")
            flash('Error registering item. Please try again.', 'error')
            return redirect(url_for('item_masterlist'))
    
    # GET method - display the masterlist
    items = Item.query.all()
    for item in items:
        # Clean the data by removing any extra whitespace
        item.label_content = ','.join(content.strip() for content in item.label_content.split(','))
        item.category = ','.join(category.strip() for category in item.category.split(','))
    return render_template('item_masterlist.html', items=items)

@app.route('/register-item', methods=['GET'])
def register_item():
    return render_template('register_item.html')

@app.route('/create-item', methods=['POST'])
def create_item():
    try:
        code_count = int(request.form['code_count'])
        
        # Create categories and label_contents lists for database
        categories = [request.form[f'category_{i}'] for i in range(1, code_count + 1)]
        label_contents = [request.form[f'label_content_{i}'] for i in range(1, code_count + 1)]
        
        # Create a new item
        new_item = Item(
            name=request.form['name'],
            revision=int(request.form['revision']),
            code_count=code_count,
            category=','.join(categories),
            label_content=','.join(label_contents),
            qr_content=f"{','.join(label_contents)}-{request.form['revision']}"
        )
        
        # Add and commit to get the ID
        db.session.add(new_item)
        db.session.commit()
        
        # If any category is 'Counting', redirect to sublot config
        if 'Counting' in categories:
            # Store the necessary data in session
            session['item_data'] = {
                'name': request.form['name'],
                'revision': int(request.form['revision']),
                'code_count': code_count,
                'categories': categories,
                'label_contents': label_contents
            }
            return redirect(url_for('sublot_config', item_id=new_item.id))
        else:
            return render_template('review_item.html', item=new_item)
            
    except Exception as e:
        db.session.rollback()
        print(f"Error creating item: {str(e)}")
        flash('Error registering item. Please try again.', 'error')
        return redirect(url_for('register_item'))

@app.route('/revise-item/<int:item_id>', methods=['GET', 'POST'])
def revise_item_page(item_id):
    item = Item.query.get_or_404(item_id)
    if request.method == 'POST':
        try:
            code_count = int(request.form['code_count'])
            
            # Get categories and label contents from form
            categories = []
            label_contents = []
            for i in range(1, code_count + 1):
                categories.append(request.form[f'category_{i}'])
                label_contents.append(request.form[f'label_content_{i}'])
            
            item.name = request.form['name']
            item.revision = int(request.form['revision'])
            item.code_count = code_count
            item.category = ','.join(categories)
            item.label_content = ','.join(label_contents)
            item.qr_content = f"{','.join(label_contents)}-{request.form['revision']}"
            item.updated_at = datetime.utcnow()
            
            db.session.commit()
            flash('Item updated successfully!', 'success')
            return redirect(url_for('item_masterlist'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error updating item: {str(e)}")
            flash('Error updating item. Please try again.', 'error')
            
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
    # Get the item data from session
    item_data = session.get('item_data', {})
    
    # Get categories and label contents
    categories = item_data.get('categories', [])
    label_contents = item_data.get('label_contents', [])
    
    # Create a list of counting categories with their label contents
    counting_items = []
    for i, (category, label) in enumerate(zip(categories, label_contents)):
        if category == 'Counting':
            counting_items.append({
                'label': label,
                'index': i + 1
            })
    
    return render_template('sublot_config.html', 
                         item_id=item_id,
                         counting_items=counting_items)

@app.route('/revise_item/<int:item_id>', methods=['POST'])
def revise_item(item_id):
    # Get the item data from session
    item_data = session.get('item_data', {})
    categories = item_data.get('categories', [])
    
    # Initialize dictionaries to store configurations
    enabled_sublots = {}
    serial_numbers = {}
    
    # Collect data for each counting category
    counting_index = 1
    for i, category in enumerate(categories):
        if category == 'Counting':
            # Check if this sublot is enabled
            enabled = request.form.get(f'enable_sublot_{counting_index}') == 'on'
            enabled_sublots[i] = enabled
            
            # Get serial number if enabled
            if enabled:
                serial_number = request.form.get(f'serial_numbers_{counting_index}')
                if serial_number:
                    serial_numbers[i] = serial_number
            
            counting_index += 1
    
    # Get the item
    item = Item.query.get_or_404(item_id)
    
    # Store the data in session for later use
    session['sublot_config'] = {
        'enabled_sublots': enabled_sublots,
        'serial_numbers': serial_numbers
    }
    
    # Render the review page with the configuration data
    return render_template('review_item.html', 
                         item=item,
                         enabled_sublots=enabled_sublots,
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

@app.route('/assembly-login', methods=['GET', 'POST'])
def assembly_login():
    if request.method == 'POST':
        # Store the form data in session
        session['item_name'] = request.form['item_name']
        session['po_number'] = request.form['po_number']
        session['total_qty'] = request.form['total_qty']
        
        return redirect(url_for('scan_article'))
        
    return render_template('assembly_login.html')

@app.route('/scan-article')
def scan_article():
    # Get the stored data from session
    item_name = session.get('item_name')
    po_number = session.get('po_number')
    
    if not item_name or not po_number:
        flash('Please complete the assembly login first', 'error')
        return redirect(url_for('assembly_login'))
        
    return render_template('scan_article.html', 
                         item_name=item_name, 
                         po_number=po_number)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
