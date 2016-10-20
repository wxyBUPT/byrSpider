# -*- coding: utf-8 -*-
__author__ = 'xiyuanbupt'
# e-mail : xywbupt@gmail.com

import collections

import scrapy
from scrapy.http import Request

from wikipedia.util.url_gen import UrlGenerator
from wikipedia.items import PageItem

class WikiSpider(scrapy.Spider):

    name = "wiki"
    allowed_domains = ["en.wikipedia.org"]
    start_urls = (
    )

    end_href = "/wiki/Philosophy"
    end_count = 500

    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip,deflate",
        "Accept-Language": "en-US,en;q=0.8,zh-TW;q=0.6,zh;q=0.4",
        "Connection": "keep-alive",
        "Content-Type":" application/x-www-form-urlencoded; charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36",
        "HOST":'m.byr.cn'
    }

    url_gen = UrlGenerator()

    path = collections.defaultdict(list)
    finish = collections.defaultdict(bool)
    reason = collections.defaultdict(str)
    visited = set()

    def __init__(self,stats,*args,**kwargs):
        super(WikiSpider,self).__init__(*args,**kwargs)
        self.stats = stats
    #重写了父类的from_crawler 方法
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = cls(crawler.stats,*args,**kwargs)
        spider._set_crawler(crawler)
        return spider

    def start_requests(self):
        url, name = self.url_gen.get_next()
        self.visited.add(name)
        self.path[name].append(name)
        yield Request(url,
                      callback=self.parse,
                      meta={'start_key':name}
                      )

    def parse(self, response):
        self.stats.inc_value("total_page", 1, 0)
        start_key = response.meta['start_key']
        content = response.css("#mw-content-text")
        ps = content.xpath('p')
        next_href = None

        for p in ps:
            atags = p.xpath('a')
            if not next_href:
                for atag in atags:
                    href = atag.xpath('@href')[0].extract()
                    if href.startswith('/wiki'):
                        next_href = href
                        break

        print u"next_href : " + next_href

        if not next_href:
            self.finish[start_key] = False
            self.reason[start_key] = 'dead_link'
            page_item = PageItem()
            page_item['start_url'] = start_key
            page_item['path'] = self.path[start_key]
            page_item['find'] = False
            page_item['reason'] = 'dead_link'
            yield page_item
            url,name = self.url_gen.get_next()
            self.visited.add(name)
            self.path[name].append(name)
            yield Request(
                url, callback=self.parse,
                meta={'start_key':name}
            )
        else:
            name = next_href.split('/')[-1]
            if name in self.visited:
                finded_key = None
                for key in self.path:
                    if name in self.path[key]:
                        index = self.path[key].index(name)
                        self.path[start_key] = self.path[start_key] + self.path[key][index:]
                        finded_key = key
                        break
                if not finded_key:
                    print u'出现了bug，在parse这里，很容易找到!!!!!!!!!!!'
                page_item = PageItem()
                page_item['start_url'] = start_key
                page_item['path'] = self.path[start_key]
                page_item['find'] = self.finish[finded_key]
                if finded_key == start_key:
                    page_item['reason'] = 'linking_circle'
                    self.reason[finded_key] = 'linking_circle'
                else:
                    page_item['reason'] = self.reason[finded_key]
                yield page_item
                self.finish[start_key] = self.finish[finded_key]
                self.reason[start_key] = self.reason[finded_key]
                finish = False
                if page_item['find']:
                    self.stats.inc_value('find',1,0)
                    if self.stats.get_value('find') >= self.end_count:
                        finish = True
                if not finish:
                    url,name = self.url_gen.get_next()
                    self.visited.add(name)
                    self.path[name].append(name)
                    yield Request(
                        url,callback=self.parse,
                        meta={'start_key':name}
                    )
            else:
                if next_href == self.end_href:
                    page_item = PageItem()
                    page_item['start_url'] = start_key
                    page_item['path'] = self.path[start_key]
                    page_item['find'] = True
                    page_item['reason'] = 'find'
                    yield page_item
                    self.finish[start_key] = True
                    self.reason[start_key] = 'find'
                    self.stats.inc_value('find',1,0)
                    if self.stats.get_value('find') < self.end_count:
                        url,name = self.url_gen.get_next()
                        self.visited.add(name)
                        self.path[name].append(name)
                        yield Request(
                            url,callback=self.parse,
                            meta={'start_key':name}
                        )
                else:
                    self.visited.add(name)
                    self.path[start_key].append(name)
                    next_url = "https://en.wikipedia.org" + next_href
                    yield Request(
                        next_url,callback=self.parse,
                        meta={'start_key':start_key}
                    )
        pass

if __name__ == "__main__":
    url_gen = UrlGenerator()
    print(u"called")
    i = 100
    while i > 0:
        print url_gen.get_next()
        i = i - 1
