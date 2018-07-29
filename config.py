import os

# 获取当前文件夹路径。相当于Unix的pwd命令
base_dir = os.path.abspath(os.path.dirname(__file__))

# 如果在代码里写配置的话，最好要用python manage.py而不是flask run(这个要export环境变量才生效，代码里的config在flsak run后没有作用)。
# 为此，我查了资料，写了篇文章: http://www.cnblogs.com/allen2333/，就是要区分 app.debug=True, python manage.py 和 export FLASK_DEBUG=True, flask run的不同。

class Config:
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    POSTS_PER_PAGE = 5
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess'

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    # 注意ENV这个变量:This is set by the FLASK_ENV environment variable and may not behave as expected if set in code. 实践看出，在代码中设置ENV并没有什么用.
    ENV = 'development'
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(base_dir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class TestingConfig(Config):
    TESTRING = True
    CSRF_ENABLED = False


class ProductionConfig(Config):
    # 注意ENV这个变量:This is set by the FLASK_ENV environment variable and may not behave as expected if set in code. 实践看出，在代码中设置ENV并没有什么用
    ENV = 'production'
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(base_dir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}
