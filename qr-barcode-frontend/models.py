from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    middle_name = db.Column(db.String(50))
    surname = db.Column(db.String(50), nullable=False)
    section = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, **kwargs):
        if 'role' in kwargs:
            if kwargs['role'] not in ['Admin', 'Assembly']:
                raise ValueError("Role must be either 'Admin' or 'Assembly'")
        super(User, self).__init__(**kwargs) 