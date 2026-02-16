from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError, DataRequired, EqualTo

from .models import User

class ForgotPasswordForm(FlaskForm):
    email = StringField(validators=[InputRequired(), Length(min=2)])
    submit = SubmitField("Reset")

class VerifyEmailForm(FlaskForm):
    submit = SubmitField("Verify Email")

class DeleteAccountForm(FlaskForm):
    submit= SubmitField("Delete Account")

class RegisterForm(FlaskForm):
    firstname = StringField(validators=[InputRequired(), Length(min=2, max=20)])
    lastname = StringField(validators=[InputRequired(), Length(min=2, max=20)])
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)])
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)])
    character_name = StringField(validators=[InputRequired(), Length(min=2, max=20)])
    email = StringField(validators=[InputRequired(), Length(min=5, max=120)])
    submit = SubmitField("Register")

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("User already exists. Create a new one or login.")

class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)])
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)])
    submit = SubmitField("Login")

class ResetPasswordForm(FlaskForm):
    password = PasswordField("New Password", validators=[DataRequired()])
    password2 = PasswordField("Repeat Password", validators=[DataRequired(), EqualTo("password", message="Passwords must match.")])
    submit = SubmitField("Confirm Reset")
