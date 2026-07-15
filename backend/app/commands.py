import click
import secrets
from pathlib import Path
from flask.cli import with_appcontext
from app.extensions import db
from app.models.user import User
from app.utils.security import hash_password
from app.services.minio_service import minio_service
from app.services.wiki_import_service import WikiImportService


@click.command('create-admin')
@click.argument('username')
@click.argument('email')
@click.argument('password')
@click.argument('is_superuser', default='false')
@with_appcontext
def create_admin(username, email, password, is_superuser):
    """Crea un nuevo usuario administrador."""
    if User.query.filter_by(email=email).first():
        click.secho(f'Error: User {email} already exists.', fg='red')
        return
    if User.query.filter_by(username=username).first():
        click.secho(f'Error: Username {username} already exists.', fg='red')
        return

    is_super = str(is_superuser).lower() == 'true'

    try:
        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            is_active=True,
            is_superuser=is_super
        )
        db.session.add(user)
        db.session.commit()
        role = 'Super Admin' if is_super else 'Admin'
        click.secho(f'{role} {username} created successfully.', fg='green')
    except Exception as e:
        db.session.rollback()
        click.secho(f'Error creating user: {e}', fg='red')


@click.command('rotate-secret')
def rotate_secret():
    """Genera un nuevo SECRET_KEY seguro."""
    click.secho('WARNING: Changing the secret key will invalidate all active sessions and signed tokens.', fg='yellow')
    click.echo('New Secret Key (copy to .env):')
    click.secho(secrets.token_hex(32), fg='green', bold=True)


@click.command('init-bucket')
@with_appcontext
def init_bucket():
    """Inicializa/Verifica el bucket de MinIO."""
    try:
        minio_service.ensure_bucket_exists()
        click.secho(f"Bucket '{minio_service.bucket_name}' verified/created successfully.", fg='green')
    except Exception as e:
        click.secho(f"Error initializing bucket: {e}", fg='red')


@click.command('import-wiki-data')
@click.argument('filepath')
@click.option('--dry-run', is_flag=True, default=False, help='Simular sin escribir cambios.')
@click.option('--update-existing', is_flag=True, default=False, help='Actualizar artículos existentes.')
@click.option('--download-images', is_flag=True, default=False, help='Descargar imágenes remotas a MinIO.')
@click.option('--publish', is_flag=True, default=False, help='Publicar artículos válidos.')
@click.option('--continue-on-error', is_flag=True, default=False, help='Continuar tras errores.')
@with_appcontext
def import_wiki_data(filepath, dry_run, update_existing, download_images, publish, continue_on_error):
    """Importa artículos desde un archivo JSON legado (data/db.json)."""
    path = Path(filepath)
    if not path.exists():
        click.secho(f"Error: File not found: {filepath}", fg='red')
        return

    click.echo(f"Importando desde: {filepath}")
    report = WikiImportService.import_json(
        str(path),
        dry_run=dry_run,
        update_existing=update_existing,
        download_images=download_images,
        publish=publish,
        continue_on_error=continue_on_error,
    )

    click.echo(f"\nArtículos leídos: {report['read']}")
    click.echo(f"Creados: {report['created']}")
    click.echo(f"Actualizados: {report['updated']}")
    click.echo(f"Omitidos: {report['skipped']}")
    click.echo(f"Errores: {report['errors']}")
    click.echo(f"Imágenes importadas: {report['imported_images']}")

    if report['error_details']:
        click.secho("\nDetalles de errores:", fg='yellow')
        for detail in report['error_details']:
            click.echo(f"  - {detail}")