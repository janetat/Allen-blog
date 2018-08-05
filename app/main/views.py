from app.main import main
from app import db
from flask import render_template, flash, redirect, url_for, request, current_app, g
from flask_login import login_user, logout_user, current_user, login_required
from .forms import LoginForm, RegistrationForm, EditProfileForm, PostForm, SearchForm
from app.models import User, Post
from werkzeug.urls import url_parse
from datetime import datetime


@main.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        # 不用db.session.add的原因是每次current_user都会调用@login_manager.user_loader(在models.py)里，里面有query.
        db.session.commit()
        # 初始化全文搜索表单，但是只有登录的用户才可以在任意页面看见。存在g里面。
        # g variable is specific to each request and each client
        # 并且模板的context可以用g
        g.search_form = SearchForm()

# 主页
# 被login_required修饰的view function, 如果没有登录，则跳转到login_manager.login_view，且URL后面添加一个参数：next
@main.route('/', methods=['GET', 'POST'])
@main.route('/index/', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, body=form.body.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('You added a new post!')
        return redirect(url_for('main.index'))

    # 分页功能由Flask-SQLAlchemy提供的paginate方法完成, paginate返回的是Pagination对象,里面有has_next, has_prev, next_num, prev_num
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    # url_for, if the names of those arguments are not referenced in the URL directly, then Flask will include them in the URL as query arguments.
    next_url = url_for('main.index', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) if posts.has_prev else None
    return render_template('index.html', title='Home page', form=form, posts=posts.items, next_url=next_url, prev_url=prev_url)

# 登录
@main.route('/login/', methods=['GET', 'POST'])
def login():
    # 如果用户已认证，则重定向到主页
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()

    # 如果表单都在提交的时候通过了validators, 那么执行以下代码。注意：每次表单提交都会发起新的请求到<form action="xxxx'>中的xxx。
    if form.validate_on_submit():
        # 利用表单的数据到数据库中查找
        user = User.query.filter_by(username=form.username.data).first()
        # 如果找不到用户或者密码错误
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('main.login'))
        # flask_login.login_user，真正的登录函数：帮这个用户注册登录状态
        login_user(user, remember=form.remember_me.data)

        # 1. 如果URL中没有next的参数，即重定向到main.index.
        # 2. 如果URL中有next参数，且next的值是相对的地址，即重定向到那个地址
        # 3. 如果URL中有next参数，且next的值是绝对的地址，即重定向到main.index, 这样做的原因是防止访问恶意网站，把请求禁锢在本app中。
        next_page = request.args.get('next')
        # 没有next和有next,但是next的值是绝对的地址
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)

    return render_template('login.html', title='Sign In', form=form)

# 登出
@main.route('/logout/')
def logout():
    # flask_login.logout_user(), 取消登录状态
    logout_user()
    return redirect(url_for('main.index'))

# 注册
@main.route('/register/', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegistrationForm()

    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Register', form=form)

# 查看user profile
@main.route('/user/<username>/')
@login_required
def user_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.user_profile', username=user.username, page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.user_profile', username=user.username, page=posts.prev_num) if posts.has_prev else None
    return render_template('profile.html', user=user, posts=posts.items, next_url=next_url, prev_url=prev_url )

# 编辑user profile
@main.route('/edit_profile/', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        # 不用db.session.add，因为每次调用current_user都会触发被@login_manager.user_loader修饰的函数(在models.py里面)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.user_profile', username=current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form=form)

# 关注
@main.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()

    if user is None:
        flash('User {} not found.').format(username)
        return redirect(url_for('main.index'))

    if user == current_user:
        flash('You can not follow yourself')
        return redirect(url_for('main.user_profile', username=username))

    current_user.follow(user)
    db.session.commit()
    flash('You are now following {}!'.format(username))
    return redirect(url_for('main.user_profile', username=username))


# 取关
@main.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()

    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('main.index'))

    if user == current_user:
        flash('You can not unfollow yourself!')
        return redirect(url_for('main.user_profile', username=username))

    current_user.unfollow(user)
    db.session.commit()
    flash('unfollowing {} successful!'.format(username))
    return redirect(url_for('main.user_profile', username=username))

# 发现
@main.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    # url_for,if the names of those arguments are not referenced in the URL directly, then Flask will include them in the URL as query arguments.
    next_url = url_for('main.explore', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) if posts.has_prev else None
    return render_template('explore.html', title='Explore', posts=posts.items, next_url=next_url, prev_url=prev_url)

# 全文搜索
# export ELASTICSEARCH_URL='http://localhost:9200'且开启Elasticsearch
@main.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.explore'))
    page = request.args.get('page', 1, type=int)
    posts, total = Post.search(g.search_form.q.data, page,
                               current_app.config['POSTS_PER_PAGE'])
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title='Search', posts=posts,
                           next_url=next_url, prev_url=prev_url)

# 扫过名字，显示profile的弹出窗
@main.route('/user/<username>/popup')
@login_required
def user_popup(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user_popup.html', user=user)