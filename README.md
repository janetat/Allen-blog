# Allen_blog
a blog system powered by Flask.

Learn by doing.

# Features
1. 鼠标hover 名字 --> 弹出个人profile框(AJAX)
2. 全文搜索(Full-text search)，用Elasticsearch和SQLALchemy实现
3. 发送私信
4. 动态提醒私信(自动更新未读私信数字)，用polling(AJAX)实现. 


# How to run
Run the app
```
export FLASK_APP=manage.py
flask run
```

Reuqirements
```
pip install -r requirements.txt
```

Database init:
```
flsak db migrate
flask db upgrade
```

Enable Full-text search, supposed to run the app for the first time
```
export ELASTICSEARCH_URL='http://localhost:9200' and fire up Elasticsearch
(Ingore it if not the 1st time)On command line, type "Post.reindex()" to initialize posts in Elasticsearch  
```

Fake users and posts, on command line:
```
from app.fake.py import fake_users, fake_posts
fake_users(100)
fake_posts(1000)
```

# 问题
1.  此处的Flask-Bootstrap的Bootstrap版本是v3的。v3和v4有地方用法不同。

如果要手动导入v4的，就要
```
{% block styles %}
    cdn link
{% endblock%}
```

# Ref
1.  [miguelgrinberg/flasky](https://github.com/miguelgrinberg/flasky)
2.  [The Flask Mega Tutorial](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xiv-ajax)
