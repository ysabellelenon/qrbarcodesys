from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from models import db, User
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'QRBARCODE_KEY'

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///qr_barcode.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db.init_app(app)

# Create tables
with app.app_context():
    db.drop_all()
    db.create_all()

# Home route redirects to login
@app.route('/')
def home():
    return redirect(url_for('login'))

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
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

# Engineering Log In Interface (Admin)
@app.route('/engineering')
def engineering_interface():
    return render_template('engineer_login.html')

# Update the manage accounts route
@app.route('/account-settings')
def account_settings():
    return render_template('account_settings.html')

# Item Masterlist page
@app.route('/item-masterlist')
def item_masterlist():
    # Sample data for display (replace with data from your database or API)
    items = [
        {"no": 1, "name": "MX55J04C0019311", "rev": 3, "content": "K1PY04Y00314_-"},
        # Additional items can be added here
    ]
    return render_template('item_masterlist.html', items=items)

# Placeholder route for new item registration or revision
@app.route('/new-register')
def new_register():
    return redirect(url_for('item_registration'))

@app.route('/revise-item')
def revise_item():
    return redirect(url_for('item_registration'))

@app.route('/logout', methods=['POST'])
def logout():
    return redirect(url_for('login'))

@app.route('/manage-accounts')
def manage_accounts():
    users = User.query.all()
    return render_template('manage_accounts.html', users=users)

@app.route('/new-account')
def new_account():
    return render_template('new_account.html')

@app.route('/delete-users', methods=['POST'])
def delete_users():
    user_ids = request.form.getlist('user_ids[]')
    for user_id in user_ids:
        user = User.query.get(user_id)
        if user:
            db.session.delete(user)
    db.session.commit()
    return redirect(url_for('manage_existing_accounts'))

@app.route('/edit-user/<int:user_id>')
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('edit_user.html', user=user)

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
            print(f"Error creating account: {str(e)}")  # For debugging
            flash('Error creating account. Please try again.', 'error')
            
    return redirect(url_for('manage_accounts'))

if __name__ == '__main__':
    app.run(debug=True)
