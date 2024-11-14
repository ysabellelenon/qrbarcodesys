from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

app = Flask(__name__)
app.secret_key = 'QRBARCODE_KEY'

# Dummy admin user data (you can store this in a database for production)
admin_user = {
    'username': 'admin',
    'password': 'password'  # In production, store a hashed password (not plaintext)
}

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
        
        # Check if credentials match the admin account
        if username == admin_user['username'] and password == admin_user['password']:
            flash("Login successful!", "success")
            return redirect(url_for('engineering_interface'))
        else:
            flash("Login failed. Please try again.", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')

# Admin registration page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Ensure both username and password are provided
        if not username or not password:
            return jsonify({'error': 'Username and password are required!'}), 400
        
        # Check if admin account already exists
        if admin_user['username'] == username:
            return jsonify({'error': 'Admin account already exists.'}), 400
        
        # Register the admin account
        admin_user['username'] = username
        admin_user['password'] = password
        
        # Return success response with redirect URL
        return jsonify({
            'message': 'Admin registered successfully!',
            'redirect': url_for('login')
        }), 200

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
