from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app import app, db  # Імпортуємо ваш `app` і `db` з основного файлу

migrate = Migrate(app, db)

if __name__ == "__main__":
    from flask.cli import FlaskGroup
    cli = FlaskGroup(app)
    cli()
