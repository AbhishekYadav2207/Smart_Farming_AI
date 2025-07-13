from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
import json

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

    return app

