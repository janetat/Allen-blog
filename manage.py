from app import create_app
import os

app = create_app(os.getenv('CONFIG') or 'default')

if __name__ == '__main__':
    app.run()