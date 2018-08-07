from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from hashlib import md5
from app.search import add_to_index, remove_from_index, query_index


class SearchableMixin(object):
    '''
        glue layer between SQLALchemy and Elasticsearch，实现自动更新两边数据库
        model Post继承这个Mixin, 被赋予这个mixin的能力

        before_commit, after_commit 里面的commit指的是SQLALchemy session(即数据库中的事务，不同于HTTP的session)的commit

        reindex的index指的是Elasticsearch中的术语
    '''

    @classmethod
    def search(cls, expression, page, per_page):
        '''
        :param expression:
        :param page:
        :param per_page:
        :return: 根据Elatsticsearch的id得到相对应的SQLAlchemy对象， 和总结果数
        '''
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return cls.query.filter_by(id=0), 0
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        # SQL的in, case语句, ensures that the results from the database come in the same order as the IDs are given.
        return cls.query.filter(cls.id.in_(ids)).order_by(
            db.case(when, value=cls.id)), total

    @classmethod
    def before_commit(cls, session):
        '''
            session.new, session.dirty, session.deleted都是sqlalchemy.orm.session自带的，当commit完session时会消失
            所以用session._changes保存状态(added, modified and deleted objects)
            在commit后update the Elasticsearch index
        '''
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls):
        # 例如Post.query, 用for遍历这个可迭代对象，就可得到所有的Post对象
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)


# SQLAlchemy自带的事件模型
db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)

# following和followed的关联表(第三张表), 因为是自引用关系(都是指向User表)，没有data只有foreign keys，所以不用model class.
followers = db.Table('followers',
                     db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
                     db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
                     )


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    # user.posts relationship is a query that is already set up by SQLAlchemy as a result of the db.relationship() definition in the User model.
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

    # 与私信相关的字段
    messages_sent = db.relationship('Message', foreign_keys='Message.sender_id', backref='author', lazy='dynamic')
    messages_received = db.relationship('Message', foreign_keys='Message.recipient_id', backref='recipient', lazy='dynamic')
    last_message_read_time = db.column(db.DateTime)

    # 返回用户有多少条新的私信。例如应用在导航栏提醒用户有多少条新的私信。
    def how_many_new_messages(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return Message.query.filter_by(recipient=self).filter(Message.timestamp > last_read_time).count()

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


class Post(SearchableMixin ,db.Model):
    __tablename__ = 'post'
    __searchable__ = ['body']
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(32), index=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post {}>'.format(self.title)

# 私信数据库模型
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    body = db.Column(db.String(140))
    # SQLALchemy的index=True就是CREATE INDEX 语句
    # what was the last time users read their private messages
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return '<Message {}>'.format(self.body)