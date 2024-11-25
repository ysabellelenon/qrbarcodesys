from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, make_response, send_file, send_from_directory
from models import db, User, Item
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
from functools import wraps
from flask import abort
import click
from flask.cli import with_appcontext

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
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        
        if user and check_password_hash(user.password, request.form['password']):
            session['user_role'] = user.role
            
            # Set redirect based on role
            if user.role == 'Admin':
                redirect_url = url_for('engineering_interface')
            elif user.role == 'Assembly':
                redirect_url = url_for('assembly_login')
            else:
                return jsonify({
                    'error': 'Invalid user role'
                }), 401

            return jsonify({
                'message': 'Login successful!',
                'redirect': redirect_url,
                'role': user.role,
                'token': generate_session_token()
            }), 200

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
            # First check if username already exists
            existing_user = User.query.filter_by(username=request.form['username']).first()
            if existing_user:
                flash('Username already exists. Please choose a different username.', 'error')
                return redirect(url_for('new_account'))

            # Check if all required fields are present
            required_fields = ['username', 'password', 'first_name', 'surname', 'section', 'role']
            for field in required_fields:
                if not request.form.get(field):
                    flash(f'{field.replace("_", " ").title()} is required.', 'error')
                    return redirect(url_for('new_account'))

            new_user = User(
                first_name=request.form['first_name'],
                middle_name=request.form.get('middle_name', ''),
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
    try:
        user_ids = request.form.getlist('user_ids[]')
        deleted_count = 0
        for user_id in user_ids:
            user = User.query.get(user_id)
            if user:
                db.session.delete(user)
                deleted_count += 1
        
        db.session.commit()
        
        # Flash appropriate message based on number of users deleted
        if deleted_count == 1:
            flash('Account has been deleted successfully.', 'success')
        elif deleted_count > 1:
            flash(f'{deleted_count} accounts have been deleted successfully.', 'success')
            
    except Exception as e:
        db.session.rollback()
        flash('Error deleting account(s). Please try again.', 'error')
        
    return redirect(url_for('manage_accounts'))

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
    # Check if we're coming back from sublot_config
    if request.args.get('preserve_state') and 'item_data' in session:
        item_data = session.get('item_data', {})
        return render_template('register_item.html', 
                             preserved_data={
                                 'name': item_data.get('name'),
                                 'revision': item_data.get('revision'),
                                 'code_count': item_data.get('code_count'),
                                 'categories': item_data.get('categories', []),
                                 'label_contents': item_data.get('label_contents', [])
                             })
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

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_role') != 'Admin':
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function

def assembly_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_role') != 'Assembly':
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function

# Protect admin routes
@app.route('/engineering')
@admin_required
def engineering_interface():
    # Clear any existing flash messages and session data we don't need
    session.pop('_flashes', None)  # This will clear all flash messages
    return render_template('engineer_login.html')

# Protect assembly routes
@app.route('/assembly-login', methods=['GET', 'POST'])
@assembly_required
def assembly_login():
    if request.method == 'POST':
        session['item_name'] = request.form['item_name']
        session['po_number'] = request.form['po_number']
        session['total_qty'] = request.form['total_qty']
        return redirect(url_for('scan_item'))
    return render_template('assembly_login.html')

@app.route('/scan-item', methods=['GET', 'POST'])
def scan_item():
    # Get all the stored data from session
    item_name = session.get('item_name')
    po_number = session.get('po_number')
    lot_number = session.get('lot_number')
    content = session.get('content')
    qty_per_box = session.get('qty_per_box')
    
    if not all([item_name, po_number, lot_number]):
        flash('Please complete the previous steps first', 'error')
        return redirect(url_for('assembly_login'))
        
    return render_template('scan_item.html', 
                         item_name=item_name, 
                         po_number=po_number,
                         lot_number=lot_number,
                         content=content,
                         qty_per_box=qty_per_box)

@app.route('/scan-article', methods=['GET', 'POST'])
def scan_article():
    if request.method == 'POST':
        # Store the article details in session
        session['lot_number'] = request.form.get('lot_number')
        session['content'] = request.form.get('article_label')
        session['qty_per_box'] = request.form.get('qty_per_box')
        
        # Make sure we have all required data
        if not all([session.get('lot_number'), session.get('content'), session.get('qty_per_box')]):
            flash('Please fill in all required fields', 'error')
            return redirect(url_for('scan_article'))
            
        return redirect(url_for('scan_item'))
    
    # Get the stored data from session for GET request
    item_name = session.get('item_name')
    po_number = session.get('po_number')
    
    if not item_name or not po_number:
        flash('Please complete the assembly login first', 'error')
        return redirect(url_for('assembly_login'))
        
    return render_template('scan_article.html', 
                         item_name=item_name, 
                         po_number=po_number)

# Add this new route
@app.route('/account-settings')
@admin_required  # Protect this route for admin users only
def account_settings():
    return render_template('account_settings.html')

@app.route('/new-account')
@admin_required  # Protect this route for admin users only
def new_account():
    return render_template('new_account.html')

@click.command('create-user')
@with_appcontext
@click.option('--username', required=True, help='Username for the new user')
@click.option('--password', required=True, help='Password for the new user')
@click.option('--first-name', required=True, help='First name of the user')
@click.option('--surname', required=True, help='Surname of the user')
@click.option('--section', required=True, help='Section of the user')
@click.option('--role', required=True, type=click.Choice(['Admin', 'Assembly'], case_sensitive=True), help='Role of the user')
@click.option('--middle-name', default='', help='Middle name of the user (optional)')
def create_user_command(username, password, first_name, surname, section, role, middle_name):
    """Create a new user via CLI."""
    try:
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            click.echo(f'Error: Username {username} already exists')
            return

        user = User(
            username=username,
            password=generate_password_hash(password),
            first_name=first_name,
            middle_name=middle_name,
            surname=surname,
            section=section,
            role=role
        )
        db.session.add(user)
        db.session.commit()
        click.echo(f'Successfully created user: {username}')
    except Exception as e:
        click.echo(f'Error creating user: {str(e)}')
    
    # # Basic usage
    # flask create-user --username ricky --password secretpass --first-name Ricky --surname Lenon --section Engineering --role Admin

    # # With optional middle name
    # flask create-user --username john_doe --password secretpass --first-name John --middle-name Robert --surname Doe --section Engineering --role Admin


# Register the command with Flask
app.cli.add_command(create_user_command)

# Add MIME type for manifest.json
@app.after_request
def add_header(response):
    if 'manifest.json' in request.path:
        response.headers['Content-Type'] = 'application/manifest+json'
    return response

@app.route('/api/sync', methods=['POST'])
def sync_data():
    try:
        # Handle syncing of offline data
        offline_data = request.json
        
        # Process each queued item
        for item in offline_data.get('queue', []):
            # Handle different types of queued actions
            if item['type'] == 'scan':
                process_offline_scan(item['data'])
            elif item['type'] == 'login':
                process_offline_login(item['data'])
                
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Add this helper function if you want to use tokens
def generate_session_token():
    return os.urandom(24).hex()

@app.route('/sw.js')
def service_worker():
    response = make_response(send_from_directory('static', 'sw.js'))
    response.headers['Content-Type'] = 'application/javascript'
    response.headers['Service-Worker-Allowed'] = '/'
    return response

if __name__ == '__main__':
    app.run(debug=True, port=5001)




