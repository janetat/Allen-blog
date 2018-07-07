from flask import Flask

from config import config

# 工厂函数，根据config生成app
def create_app(config_name):
    # 生成Flask实例
    app = Flask(__name__)

    # 从类中导入配置config, 用来配置app
    app.config.from_object(config[config_name])

    # 注册蓝图（Flask模块化）
    from app.main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
