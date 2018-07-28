from random import randint
from sqlalchemy.exc import IntegrityError
from faker import Faker
from app import db
from .main.models import User, Post
from werkzeug.security import generate_password_hash

def fake_users(count=100):
    fake = Faker()
    i = 0
    while i < count:
        u = User(
            username=fake.user_name(),
            email=fake.email(),
            password_hash=generate_password_hash('x'),
            )
        db.session.add(u)
        try:
            db.session.commit()
            i += 1
        except IntegrityError:
            db.session.rollback()


def fake_posts(count=100):
    fake = Faker()
    user_count = User.query.count()
    for i in range(count):
        u = User.query.offset(randint(0, user_count - 1)).first()
        p = Post(
            title=fake.name(),
            body=fake.text(),
            author=u)
        db.session.add(p)
    db.session.commit()
