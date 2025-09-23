from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
import json
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    from app.auth.routes import auth_bp
    from app.farmer.routes import farmer_bp
    from app.government.routes import govt_bp
    from app.admin.routes import admin_bp
    from app.farmer.routes import main_bp
    from app.auth.routes import api_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(farmer_bp, url_prefix='/farmer')
    app.register_blueprint(govt_bp, url_prefix='/government')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    @app.template_filter('loads')
    def json_loads_filter(s):
        try:
            return json.loads(s)
        except Exception:
            return {}
        
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA busy_timeout = 5000;")  # wait 5s before "database locked"
        cursor.close()

    return app
