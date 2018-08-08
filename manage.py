import os
from app import create_app, db
from app.models import User, Post, Notification, Message
from app.fake import fake_users, fake_posts


app = create_app(os.getenv('CONFIG') or 'production')


@app.shell_context_processor
def make_shell_context():
    return {'db':db, 'User':User, 'Post':Post, 'fake_users':fake_users, 'fake_posts':fake_posts, 'Message':Message, 'Notification':Notification}

if __name__ == '__main__':
    app.run()
