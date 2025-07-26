from . import db
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import Optional, URL

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('super_admin', 'admin', 'employee'), default='employee')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class NewsArticle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300))
    url = db.Column(db.String(500))
    full_text = db.Column(db.Text)
    summary = db.Column(db.Text)
    bias = db.Column(db.String(50))
    tone = db.Column(db.String(50))
    emotion_score = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class NewsInputForm(FlaskForm):
    url = StringField("News URL", validators=[Optional(), URL()])
    raw_text = TextAreaField("Or paste article text", validators=[Optional()])
    submit = SubmitField("Analyze")



