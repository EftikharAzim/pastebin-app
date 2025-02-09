from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import hashlib
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pastes.db'
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this in production!
db = SQLAlchemy(app)

# Database model for storing pastes
class Paste(db.Model):
    id = db.Column(db.String(64), primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)  # Optional expiration

# Ensure database is created
with app.app_context():
    db.create_all()

def delete_expired_pastes():
    """Delete pastes that have expired."""
    now = datetime.utcnow()
    expired_pastes = Paste.query.filter(Paste.expires_at != None, Paste.expires_at < now).all()
    for paste in expired_pastes:
        db.session.delete(paste)
    db.session.commit()

# Error Handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', message="Page not found."), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"Server error: {error}")
    return render_template('error.html', message="An internal server error occurred."), 500

# Routes
@app.route('/', methods=['GET', 'POST'])
def index():
    """Create a new paste."""
    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        expiration_days = request.form.get('expiration', '').strip()

        if not content:
            flash('Paste content cannot be empty.', 'error')
            return redirect(url_for('index'))

        # Generate a unique ID (using the first 10 characters of a SHA256 hash)
        unique_id = hashlib.sha256(content.encode()).hexdigest()[:10]

        # Calculate expiration date if provided
        expires_at = None
        if expiration_days:
            try:
                days = int(expiration_days)
                if days > 0:
                    expires_at = datetime.utcnow() + timedelta(days=days)
            except ValueError:
                flash('Invalid expiration value. Please provide a number of days.', 'error')
                return redirect(url_for('index'))

        paste = Paste(id=unique_id, content=content, expires_at=expires_at)
        db.session.add(paste)
        db.session.commit()
        flash('Paste successfully created!', 'success')
        return redirect(url_for('show_paste', paste_id=unique_id))

    return render_template('index.html')

@app.route('/paste/<paste_id>', methods=['GET', 'POST'])
def show_paste(paste_id):
    """Display and manage a paste."""
    delete_expired_pastes()  # Clean up expired pastes on each request

    paste = Paste.query.get(paste_id)
    if not paste:
        flash('This paste has expired or does not exist.', 'error')
        return render_template('paste-deleted.html')

    if request.method == 'POST' and 'delete' in request.form:
        db.session.delete(paste)
        db.session.commit()
        flash('The paste has been successfully deleted.', 'success')
        return redirect(url_for('index'))

    return render_template('show_paste.html', paste=paste)

if __name__ == '__main__':
    app.run()  # No debug=True here
