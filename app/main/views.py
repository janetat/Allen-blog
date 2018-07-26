from app.main import main
from app import db
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from .forms import LoginForm, RegistrationForm
from .models import User
from werkzeug.urls import url_parse

# 主页
# 被login_required修饰的view function, 如果没有登录，则跳转到login_manager.login_view，且URL后面添加一个参数：next
@main.route('/')
@main.route('/index/')
@login_required
def index():
    posts = current_user.posts
    return render_template('index.html', title='allen', posts=posts)

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
@main.route('/register', methods=['GET', 'POST'])
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
@main.route('/user/<username>')
@login_required
def user_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = [
        {'author': user, 'body': 'Test post #1'},
        {'author': user, 'body': 'Test post #2'}
    ]
    return render_template('user.html', user=user, posts=posts)