# app.py

from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'QRBARCODE_KEY'

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
        
        # Simulated backend response (replace with actual API request)
        if username == "admin" and password == "password":
            flash("Login successful!", "success")
            return redirect(url_for('engineering_interface'))
        else:
            flash("Login failed. Please try again.", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')

# Engineering Log In Interface (Admin)
@app.route('/engineering')
def engineering_interface():
    return render_template('engineer_login.html')

# Placeholder for manage accounts functionality
@app.route('/manage-accounts')
def manage_accounts():
    # This can later be filled with functionality or a page template for account management
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