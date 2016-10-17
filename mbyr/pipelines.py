# -*- coding: utf-8 -*-

from mbyr.conf import ConfUtil
import pymongo

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html


class MbyrPipeline(object):
    def process_item(self, item, spider):
        return item

class SaveToMongo(object):

    def __init__(self,mongo_uri,mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls,crawler):
        return cls(
            mongo_uri = ConfUtil.get_mongo_uri(),
            mongo_db = ConfUtil.get_mongo_db()
        )

    def open_spider(self,spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self,spider):
        self.client.close()

    def process_item(self,item,spider):

        # 这里的item 设计的不好，判断type 会使用过多的cpu 资源
        s_type = item['type']
        if s_type == 'board':
            board = item.board
            pass
        elif s_type == 'top10':
            pass
        elif s_type == 'new_info':
            pass
        elif s_type == 'img':
            pass
        else:
            # 收到什么类型都不是的item
            pass

    def _saveBoard(self,item):
        pass




