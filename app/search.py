from flask import current_app

'''
    @ Elasticsearch参考：http://www.ruanyifeng.com/blog/2017/08/elasticsearch.html
    @ index, doc_type为Elasticsearch的术语。
    @ Cli Test: 
        flask shell
    >>> from app.search import add_to_index, remove_from_index, query_index
    >>> for post in Post.query.all():
         add_to_index('posts', post)
    >>> query_index('posts', 'text you wanna search', 1, 100)
    
    @ 问题1：
        query_index()返回的第一个是model id的列表，怎么转换成SQLAlchemy的model对象(这样才能在Flask中方便操作，例如在模板中渲染)？
        
    @ 问题2：
        如何联系SQLALchemy和Elasticsearch。即当更新时，如何自动更新数据库？
        
    对于两个问题，在models.py中创建SearchableMixin，这是介乎于SQLAlchemy和Elasticsearch的glue layer.
'''


# model是SQLALchemy的model。index和document_type都是Elasticsearch的术语，用index来命名。id需要unique，所以可以借用SQLALchemy的model的id。如果用这个方法添加elasticsearch已经拥有的条目，这个条目会被覆盖。且id这样用可以很方便地连接两个数据库(Elasticsearch是引擎，也可以算是数据库)。
def add_to_index(index, model):
    if not current_app.elasticsearch:
        return
    payload = {}
    for field in model.__searchable__:
        payload[field] = getattr(model, field)
    current_app.elasticsearch.index(index=index, doc_type=index, id=model.id,
                                    body=payload)


def remove_from_index(index, model):
    if not current_app.elasticsearch:
        return
    current_app.elasticsearch.delete(index=index, doc_type=index, id=model.id)


def query_index(index, query, page, per_page):
    '''
    :param index: Elasticsearch的术语
    :param query: text you wanna get
    :param page: 因为没有像SQLAlchemy的Pagination对象，所以要用'from'参数去构造算法去分页
    :param per_page: 每页的items
    :return:
    '''
    if not current_app.elasticsearch:
        return [], 0
    search = current_app.elasticsearch.search(
        index=index, doc_type=index,
        # 这些都是Elasticsearch的语法，具体看doc
        body={'query': {'multi_match': {'query': query, 'fields': ['*']}},
              'from': (page - 1) * per_page, 'size': per_page})
    # {
    # 	'took': 2,
    # 	'timed_out': False,
    # 	'_shards': {
    # 		'total': 5,
    # 		'successful': 5,
    # 		'skipped': 0,
    # 		'failed': 0
    # 	},
    # 	'hits': {
    # 		'total': 1,
    # 		'max_score': 0.2876821,
    # 		'hits': [{
    # 			'_index': 'my_index',
    # 			'_type': 'my_index',
    # 			'_id': '2',
    # 			'_score': 0.2876821,
    # 			'_source': {
    # 				'text': 'a second test'
    # 			}
    # 		}]
    # 	}
    # }
    # 列表构造式, list comprehension
    ids = [int(hit['_id']) for hit in search['hits']['hits']]
    # 返回的第一个是一个包含查询结果的列表，里面存着符合的id, 也就是SQLALChemy model的id， 。第二个是总结果数。
    return ids, search['hits']['total']

