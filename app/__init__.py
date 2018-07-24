from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import config

login_manager = LoginManager()
db = SQLAlchemy()
migrate = Migrate()

# 工厂函数，根据config生成app
def create_app(config_name):
    # 生成Flask实例
    app = Flask(__name__)

    # 从类中导入配置config, 用来配置app
    app.config.from_object(config[config_name])

    # 第三方extensions init
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'


    # 注册蓝图（Flask模块化）
    from app.main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
