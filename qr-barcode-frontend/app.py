# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key

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
            return redirect(url_for('item_registration'))
        else:
            flash("Login failed. Please try again.", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')

# Item Registration page
@app.route('/item-registration', methods=['GET', 'POST'])
def item_registration():
    if request.method == 'POST':
        item_name = request.form['item_name']
        revision_number = request.form['revision_number']
        category = request.form['category']
        label_content = request.form['label_content']

        # Simulate backend registration response (would connect to API in a full app)
        flash(f"Item '{item_name}' registered successfully!", "success")
        return redirect(url_for('item_registration'))

    return render_template('item_reg.html')

if __name__ == '__main__':
    app.run(debug=True)