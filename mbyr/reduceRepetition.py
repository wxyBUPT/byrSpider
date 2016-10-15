#coding=utf-8
__author__ = 'xiyuanbupt'
# e-mail : xywbupt@gmail.com

# 爬虫的判重复模块，定制化程度比较高
# 因为借助Redis 实现逻辑比较简单，所以判重模块借助了Redis，如果想使用其他工具（例如mongo之类），则使用其他工具的api 实现接口即可

import redis

from conf import ConfUtil


class RepReducer:

    # redis连接，静态变量
    r = redis.StrictRedis(host=ConfUtil.get_redis_host(),
                          port = ConfUtil.get_redis_port(),
                          db = ConfUtil.get_redis_db()
                          )
    # 下面定义一些常量
    # 被置顶的帖子（set:{prefix + name_space:top_url_hash}）的前缀(prefix)
    top_visited_pre = "top_visited"
    # 记录帖子最后访问索引的前缀 (hash : {prefix + url_hash:{url_hash:index}}) 的前缀(prefix)
    visited_post_hash_prefix = "hash_visited_post"

    def __init__(self):
        pass

    def is_top_visited(self, name_space, top_url_hash):
        '''
        被置顶的帖子是否被访问过
        逻辑是使用一个Set,把所有被访问到的url放入set 中
        没有访问过的url不在set 中
        :param name_space 被置顶帖子的命名空间，ex. BYRStar
        :param top_url_hash 帖子在命名空间的hash，网站直接提供 ex. 11
        :return: True: visited , False:unvisited
        '''
        return self.r.sismember(self.top_visited_pre + name_space, top_url_hash)

    def visit_top(self, name_space, top_url_hash):
        '''
        已经完成被置顶的帖子的访问
        :param name_space:
        :param top_url_hash:
        :return: null
        '''
        return self.r.sadd(self.top_visited_pre + name_space, top_url_hash)

    def get_post_last_visit_index(self, name_space, url_hash):
        '''
        获得爬虫最后访问帖子的index，如果帖子没有被访问则返回 -1
        :param name_space: 命名空间, ex. Quyi
        :param url_hash: 帖子的hash，bbs 直接提供的 ex. 13036
        :return:
        '''
        last_visit_index = self.r.hget(self.visited_post_hash_prefix + name_space,
                                       url_hash
                                       )
        if not last_visit_index:
            return -1
        else:
            return int(last_visit_index)

    def set_post_visit_index(self, name_space, url_hash, index):
        '''
        设置帖子最后被访问到的索引
        :param name_space:
        :param url_hash:
        :return:
        '''
        index = int(index)
        return self.r.hset(
            self.visited_post_hash_prefix + name_space,
            url_hash,
            index
        )




