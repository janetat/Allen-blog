import os

# 获取当前文件夹路径。相当于Unix的pwd命令
base_dir = os.path.abspath(os.path.dirname(__file__))

# 如果在代码里写配置的话，最好要用python manage.py而不是flask run(这个要export环境变量才生效，代码里的config在flsak run后没有作用)。
# 为此，我查了资料，写了篇文章: http://www.cnblogs.com/allen2333/，就是要区分 app.debug=True, python manage.py 和 export FLASK_DEBUG=True, flask run的不同。

class Config:
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = 'hard to guess'

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    ENV = 'development'
    DEBUG = True


class TestingConfig(Config):
    TESTRING = True
    CSRF_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False

    @classmethod
    def init_app(cls, app):
        pass


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}
