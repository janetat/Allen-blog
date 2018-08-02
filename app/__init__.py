from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from config import config
from app.my_extensions.file_logger import FileLogger


login_manager = LoginManager()
db = SQLAlchemy()
migrate = Migrate()
file_logger = FileLogger()
bootstrap = Bootstrap()
moment = Moment()

# 工厂函数，根据config生成app
def create_app(config_name):
    # 生成Flask实例
    app = Flask(__name__)

    # 从类中导入配置config, 用来配置app
    app.config.from_object(config[config_name])

    # extensions init
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    file_logger.init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)

    # 注册蓝图（Flask模块化）
    from app.main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from app.errors import errors as errors_blueprint
    app.register_blueprint(errors_blueprint)

    return app
