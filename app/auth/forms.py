from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models import User


class LoginForm(FlaskForm):
    """Login form."""
    email = StringField('Email', validators=[
        DataRequired(message='Email é obrigatório.'),
        Email(message='Email inválido.')
    ])
    password = PasswordField('Senha', validators=[
        DataRequired(message='Senha é obrigatória.')
    ])
    remember = BooleanField('Lembrar-me')
    submit = SubmitField('Entrar')


class RegisterForm(FlaskForm):
    """Registration form."""
    username = StringField('Nome de Usuário', validators=[
        DataRequired(message='Nome de usuário é obrigatório.'),
        Length(min=3, max=80, message='O nome deve ter entre 3 e 80 caracteres.')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email é obrigatório.'),
        Email(message='Email inválido.')
    ])
    password = PasswordField('Senha', validators=[
        DataRequired(message='Senha é obrigatória.'),
        Length(min=6, message='A senha deve ter no mínimo 6 caracteres.')
    ])
    confirm_password = PasswordField('Confirmar Senha', validators=[
        DataRequired(message='Confirmação de senha é obrigatória.'),
        EqualTo('password', message='As senhas não conferem.')
    ])
    submit = SubmitField('Criar Conta')

    def validate_username(self, field):
        user = User.query.filter_by(username=field.data).first()
        if user:
            raise ValidationError('Este nome de usuário já está em uso.')

    def validate_email(self, field):
        user = User.query.filter_by(email=field.data).first()
        if user:
            raise ValidationError('Este email já está cadastrado.')
