from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, IntegerField,
                     BooleanField, SelectField, SubmitField)
from wtforms.validators import DataRequired, Length, URL, Optional, NumberRange


class ModuleForm(FlaskForm):
    """Form for creating/editing modules."""
    title = StringField('Título do Módulo', validators=[
        DataRequired(message='Título é obrigatório.'),
        Length(max=200, message='Título deve ter no máximo 200 caracteres.')
    ])
    description = TextAreaField('Descrição', validators=[
        Optional(),
        Length(max=2000, message='Descrição deve ter no máximo 2000 caracteres.')
    ])
    order = IntegerField('Ordem', default=0, validators=[
        NumberRange(min=0, message='Ordem deve ser um número positivo.')
    ])
    is_published = BooleanField('Publicado')
    submit = SubmitField('Salvar Módulo')


class LessonForm(FlaskForm):
    """Form for creating/editing lessons."""
    module_id = SelectField('Módulo', coerce=int, validators=[
        DataRequired(message='Selecione um módulo.')
    ])
    title = StringField('Título da Aula', validators=[
        DataRequired(message='Título é obrigatório.'),
        Length(max=200, message='Título deve ter no máximo 200 caracteres.')
    ])
    description = TextAreaField('Descrição', validators=[
        Optional(),
        Length(max=2000, message='Descrição deve ter no máximo 2000 caracteres.')
    ])
    video_url = StringField('URL do Vídeo (YouTube/Vimeo)', validators=[
        Optional(),
        Length(max=500)
    ])
    content = TextAreaField('Conteúdo da Aula (HTML)', validators=[
        Optional()
    ])
    order = IntegerField('Ordem', default=0, validators=[
        NumberRange(min=0, message='Ordem deve ser um número positivo.')
    ])
    duration_minutes = IntegerField('Duração (minutos)', default=0, validators=[
        NumberRange(min=0, message='Duração deve ser um número positivo.')
    ])
    is_published = BooleanField('Publicado')
    submit = SubmitField('Salvar Aula')
