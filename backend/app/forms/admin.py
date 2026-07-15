from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    PasswordField,
    StringField,
    SubmitField,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional


class AdminUserCreateForm(FlaskForm):
    username = StringField(
        'Nombre de usuario',
        validators=[
            DataRequired(message='Campo obligatorio'),
            Length(min=3, max=64, message='Entre 3 y 64 caracteres'),
        ],
    )
    email = StringField(
        'Correo electrónico',
        validators=[
            DataRequired(message='Campo obligatorio'),
            Email(message='Email inválido'),
            Length(max=255),
        ],
    )
    password = PasswordField(
        'Contraseña temporal',
        validators=[
            DataRequired(message='Campo obligatorio'),
            Length(min=8, max=128, message='Mínimo 8 caracteres'),
        ],
    )
    confirm_password = PasswordField(
        'Confirmar contraseña',
        validators=[
            DataRequired(message='Campo obligatorio'),
            EqualTo('password', message='Las contraseñas no coinciden'),
        ],
    )
    is_superuser = BooleanField('Crear como super admin')
    submit = SubmitField('Crear administrador')


class AdminUserUpdateForm(FlaskForm):
    username = StringField(
        'Nombre de usuario',
        validators=[
            DataRequired(message='Campo obligatorio'),
            Length(min=3, max=64, message='Entre 3 y 64 caracteres'),
        ],
    )
    email = StringField(
        'Correo electrónico',
        validators=[
            DataRequired(message='Campo obligatorio'),
            Email(message='Email inválido'),
            Length(max=255),
        ],
    )
    password = PasswordField(
        'Nueva contraseña',
        validators=[
            Optional(),
            Length(min=8, max=128, message='Mínimo 8 caracteres'),
        ],
    )
    confirm_password = PasswordField(
        'Confirmar nueva contraseña',
        validators=[
            Optional(),
            EqualTo('password', message='Las contraseñas no coinciden'),
        ],
    )
    is_active = BooleanField('Usuario activo')
    submit = SubmitField('Guardar cambios')


class DeleteUserForm(FlaskForm):
    submit = SubmitField('Eliminar usuario')