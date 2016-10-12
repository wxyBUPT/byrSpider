# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class MbyrItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class FullPostItem(scrapy.Item):

    '''
    帖子名称
    发帖时间
    帖子内容
    '''
    name = scrapy.Field()
    time = scrapy.Field()
    user = scrapy.Field()
    content = scrapy.Field()
    comments = scrapy.Field()

class ImageItem(scrapy.Field):
    '''
    用来保存image 地址的
    '''
    href = scrapy.Field()
    done = scrapy.Field()