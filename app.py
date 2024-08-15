from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import hashlib

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pastes.db'
app.config['SECRET_KEY'] = 'your_secret_key'  # Required for flashing messages
db = SQLAlchemy(app)

# Database model
class Paste(db.Model):
    id = db.Column(db.String(64), primary_key=True)
    content = db.Column(db.Text, nullable=False)

# Ensure database is created within the application context
with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        content = request.form['content']
        unique_id = hashlib.sha256(content.encode()).hexdigest()[:10]
        paste = Paste(id=unique_id, content=content)
        db.session.add(paste)
        db.session.commit()
        return redirect(url_for('show_paste', paste_id=unique_id))
    return render_template('index.html')

@app.route('/paste/<paste_id>', methods=['GET', 'POST'])
def show_paste(paste_id):
    paste = Paste.query.get(paste_id)
    if paste is None:
        flash("This paste has been deleted or does not exist.")
        return render_template('paste_deleted.html')
    
    if request.method == 'POST':  # Handle delete request
        if 'delete' in request.form:
            db.session.delete(paste)
            db.session.commit()
            flash("The paste has been successfully deleted.")
            return render_template('paste_deleted.html')

    return render_template('show_paste.html', paste=paste)

if __name__ == '__main__':
    app.run(debug=True)
