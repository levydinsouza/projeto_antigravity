from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length, ValidationError
from flask_login import current_user
from app.models import User


class ProfileForm(FlaskForm):
    """Form for editing user profile and uploading profile picture."""
    username = StringField('Nome de Usuário', validators=[
        DataRequired(message='Nome de usuário é obrigatório.'),
        Length(min=3, max=80, message='Nome de usuário deve ter entre 3 e 80 caracteres.')
    ])
    email = StringField('E-mail', validators=[
        DataRequired(message='E-mail é obrigatório.'),
        Email(message='E-mail inválido.'),
        Length(max=120)
    ])
    profile_pic = FileField('Foto de Perfil', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'webp', 'gif'],
                    'Apenas arquivos de imagem são permitidos (jpg, png, webp, gif).')
    ])
    submit = SubmitField('Salvar Alterações')

    def validate_username(self, username):
        if username.data.strip() != current_user.username:
            user = User.query.filter_by(username=username.data.strip()).first()
            if user:
                raise ValidationError('Este nome de usuário já está em uso.')

    def validate_email(self, email):
        if email.data.strip().lower() != current_user.email.lower():
            user = User.query.filter_by(email=email.data.strip().lower()).first()
            if user:
                raise ValidationError('Este e-mail já está em uso.')
