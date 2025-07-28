from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import Optional, URL

class NewsInputForm(FlaskForm):
    url = StringField("News URL", validators=[Optional(), URL()])
    raw_text = TextAreaField("Or paste article text", validators=[Optional()])
    submit = SubmitField("Analyze")
