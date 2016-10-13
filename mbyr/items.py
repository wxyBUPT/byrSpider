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
    #帖子的类型，打算使用枚举型，暂时使用字符串代替，因为没有全局的创建数据库命令，所以使用字符代替
    type = scrapy.Field()
    #帖子名称，字符创
    name = scrapy.Field()
    #帖子创建的时间 datatime.datatime()
    time = scrapy.Field()
    #帖子的作者
    user = scrapy.Field()
    #帖子的内容
    content = scrapy.Field()
    #帖子的评论 []
    comments = scrapy.Field()
    #帖子的热门评论，如果有 []
    hots = scrapy.Field()
    #帖子地址
    url = scrapy.Field()

class ImageItem(scrapy.Field):
    '''
    用来保存image 地址的
    '''
    href = scrapy.Field()
    done = scrapy.Field()