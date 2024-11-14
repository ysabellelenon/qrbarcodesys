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

# Admin registration page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            # Get form data
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            username = request.form['username']
            email = request.form['email']
            role = request.form['role']
            phone = request.form['phone']
            password = request.form['password']

            # Check if username or email already exists
            if User.query.filter_by(username=username).first():
                return jsonify({'error': 'Username already exists'}), 400
            if User.query.filter_by(email=email).first():
                return jsonify({'error': 'Email already exists'}), 400

            # Create new user
            new_user = User(
                first_name=first_name,
                last_name=last_name,
                username=username,
                email=email,
                role=role,
                phone=phone,
                password=generate_password_hash(password)
            )

            # Add to database
            db.session.add(new_user)
            db.session.commit()

            return jsonify({
                'message': 'Registration successful!',
                'redirect': url_for('login')
            }), 200

        except Exception as e:
            db.session.rollback()
            print(f"Error during registration: {str(e)}")
            return jsonify({'error': 'Registration failed. Please try again.'}), 500

    return render_template('register.html')

# Engineering Log In Interface (Admin)
@app.route('/engineering')
def engineering_interface():
    return render_template('engineer_login.html')

# Placeholder for manage accounts functionality
@app.route('/manage-accounts')
def manage_accounts():
    flash("Manage Accounts page under development.", "info")
    return redirect(url_for('engineering_interface'))

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
    flash("Redirected to Item Registration for a new item.", "info")
    return redirect(url_for('item_registration'))

@app.route('/revise-item')
def revise_item():
    flash("Redirected to Item Registration to revise the selected item.", "info")
    return redirect(url_for('item_registration'))

@app.route('/logout', methods=['POST'])
def logout():
    flash("Logged out successfully.", "success")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
