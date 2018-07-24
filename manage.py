import os
from app import create_app, db
from app.main.models import User, Post


app = create_app(os.getenv('CONFIG') or 'default')

@app.shell_context_processor
def make_shell_context():
    return {'db':db, 'User':User, 'Post':Post}

if __name__ == '__main__':
    app.run()