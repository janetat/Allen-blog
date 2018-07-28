from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from hashlib import md5


# following和followed的关联表(第三张表), 因为是自引用关系(都是指向User表)，没有data只有foreign keys，所以不用model class.
followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    # 第一个参数为右边的表(因为是自引用关系，所以是自己)，secondary是两表之间的关联表(自引用关系，多对多关系必有第三张表，就是关联表)
    # backref defines how this relationship will be accessed from the right side entity(secondary table).
    # SQLAlchemy ORM，使得followed这个relationship可以当成“列表”来操作。例如,user1.followed.append(user2), user1.followed.remove(user2)
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        # 左边的表有followed, 右边的表有followers
        backref=db.backref('followers', lazy='dynamic'),
        lazy='dynamic'
    )


    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # 获取头像地址
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)

    # 关注
    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    # 取关
    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        # Post.query.join(...).filter(...).order_by(...)
        # join的第一个参数为关联表(自引用的第三张表)，第二个参数为条件
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)
        ).filter(followers.c.follower_id == self.id)

        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())

# 每次引用current_user, 都会触发这个函数
@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(32), index=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.Date, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post {}>'.format(self.title)


