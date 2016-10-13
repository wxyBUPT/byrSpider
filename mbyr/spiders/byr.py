# -*- coding: utf-8 -*-

import re
import logging
import logging.config
from datetime import datetime

logging.config.fileConfig('./logger.ini')
import scrapy
from scrapy.http import FormRequest,Request

from mbyr.items import FullPostItem,ImageItem

class ByrSpider(scrapy.Spider):

    catalogRePattern = re.compile(r'')
    pageRePattern = re.compile(r'')
    name = "byr"
    allowed_domains = ["http://m.byr.cn/","m.byr.cn"]
    start_urls = (
    )
    logger = logging.getLogger('byr')

    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip,deflate",
        "Accept-Language": "en-US,en;q=0.8,zh-TW;q=0.6,zh;q=0.4",
        "Connection": "keep-alive",
        "Content-Type":" application/x-www-form-urlencoded; charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36",
        "HOST":'m.byr.cn'
    }

    def __init__(self,stats,*args,**kwargs):
        super(ByrSpider,self).__init__(*args,**kwargs)
        self.rootDir = DirNode(u'根',False,"/")
        self.stats = stats

    #重写了父类的from_crawler 方法
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = cls(crawler.stats,*args,**kwargs)
        spider._set_crawler(crawler)
        return spider

    def start_requests(self):

        return [Request("http://m.byr.cn/",callback=self.login,meta={'cookiejar':1},headers=self.headers)]

    def login(self,response):
        request = FormRequest.from_response(
            response,
            meta = {
                'cookiejar':response.meta['cookiejar']
            },
            formdata={
                "id":"qwe1234",
                "passwd":"1402216786"
            },callback = self.afterLogin,
        )
        return request


    def afterLogin(self,response):
        '''
        获得目录结构，记录到日志中，并开始爬取数据
        :param response:
        :return:
        '''
        logger = self.logger
        logger.info(u"日志是有效的")
        print(u'处理十大')
        yield Request("http://m.byr.cn",callback=self.parseTopTen,headers=self.headers,meta={
            'cookiejar':response.meta['cookiejar'],
        },dont_filter=True)

        yield Request("http://m.byr.cn/section",callback=self.getDirTree,headers=self.headers,meta={
            'cookiejar':response.meta['cookiejar'],
            'dirParent':self.rootDir
        })

        #日志记录获得的节点
        '''
        #因为是被yield 出去的，所以不能获得 rootDir
        for dir in self.rootDir.childs:
            print dir.name
        for dir in self.rootDir.childs:
            logger.info(dir.name)
            for dir0 in dir.childs:
                logger.info("  " + dir0.name)
                for dir1 in dir0.childs:
                    logger.info("    " + dir1.name)
        #print(response.body)
        pass
        '''

    def parseTopTen(self,response):
        tmp = response.css("ul.slist:nth-child(2) > li")
        topTen = tmp[1:]
        for idx,val in enumerate(topTen):
            title = val.xpath("a/text()")[0].extract().rstrip('(')
            href = val.xpath("a/@href")[0].extract()
            vote = int(val.xpath("a/span/text()")[0].extract())
            yield Request("http://m.byr.cn" + href, callback=self.parseTop,headers=self.headers,meta={
                'cookiejar':response.meta['cookiejar'],
                'title':title,
                'i':idx,
                'vote':vote
            })

    def handle_li(self,li):
        '''
        处理有内容的li标签
        可能需要处理图片与br 标签
        handle li tag
        tag contains username,posttime content user ip
        :param li:
        :return:
        '''
        headers = li.xpath('div/div')[0].xpath('a')
        username = headers[1].xpath('text()').extract()[0]
        timestr = headers[2].xpath('text()').extract()[0]
        posttime = datetime.strptime(timestr,'%Y-%m-%d %H:%M:%S')
        '''
        打算使用两种策略，一种是直接保存html,这样的好处是可以保持原来的格式
        另外一种策略是保存文本，好处是存储空间小，但是格式不美观
        目前使用第一种策略
        第二种策略的代码同样也如下实现
        '''
        div = li.css('.sp')
        content = div.extract()
        #lines = li.css('.sp').xpath('text()').extract()
        #content = u'\n'.join(lines)
        imgs = div.xpath('img')
        imgItems = []
        for img in imgs:
            imageItem = ImageItem()
            imageItem['href'] = img.xpath('@src').extract()[0]
            imageItem['done'] = False
            imgItems.append(imageItem)
        #暂时先不处理图片
        return (username,posttime,content,imgItems)


    def parseTop(self,response):
        '''
        处理第一页内容
        :param response:
        :return:
        '''

        #获得总共多少页，与当前页
        pageInfo = response.css('.plant')[-2].xpath('text()').extract()[0]
        (currPage,totalPage) = map(lambda x:int(x),pageInfo.split(u'/'))
        print currPage, totalPage
        from scrapy.shell import inspect_response
        inspect_response(response,self)

        contents = response.css(".list")
        if len(contents) != 1:
            self.logger.error(u".list 并不是唯一的选择器，页面结构可能被改变")
            print len(contents)

        contents = contents[0].xpath('li')
        username,posttime,content,imgItems = self.handle_li(contents[1])
        #不管怎样先yield
        for imgItem in imgItems:
            yield imgItem

        fullPostItem = FullPostItem()
        fullPostItem['name'] = response.meta['title']
        fullPostItem['time'] = posttime
        fullPostItem['user'] = username
        fullPostItem['content'] = content
        fullPostItem['comments'] = [self.handle_li(li) for index,li in enumerate(contents) if index not in (0,2)]

        pass

    def parse(self, response):
        pass

    def getDirTree(self,response):
        nodes = response.css(".slist li")
        #from scrapy.shell import inspect_response
        #inspect_response(response,self)

        parent = response.meta['dirParent']

        for node in nodes:
            try:
                type = node.xpath("font/text()").extract()[0]
            except Exception :
                type = node.xpath("text()")[0].extract()
                #from scrapy.shell import inspect_response
                #inspect_response(response,self)

            name = node.xpath("a")[0].xpath('text()').extract()[0]
            href = node.xpath("a")[0].xpath('@href').extract()[0]
            if(type.startswith(u"目录")):
                tmpnode = DirNode(name,False,href)
                parent.appendChild(tmpnode)
                yield Request(tmpnode.fullUrl,callback=self.getDirTree,headers=self.headers,meta={
                    'cookiejar':response.meta['cookiejar'],
                    'dirParent':tmpnode
                })
            if(type.startswith(u"版面")):
                tmpnode = DirNode(name,True,href)
                parent.appendChild(tmpnode)
                #print(name)
                #print(href)
                #开始处理版面

class DirNode:

    def __init__(self,name,isLeaf,href):
        '''
        Consuturct
        :param name: ex. 笑口常开
        :param isLeaf: Is leaf node
        :param url: url, ex. /board/Joke
        :return:
        '''
        self.name = name
        self.isLeaf = isLeaf
        self.href = href
        self.fullUrl = 'http://m.byr.cn' + href
        self.childs = []

    def appendChild(self,dirNode):
        '''
        add sub dir
        :param dirNode:
        :return:
        '''
        self.childs.append(dirNode)

    def __str__(self):
        '''
        unicode
        :return:
        '''
        return self.name + u"isLeaf: " + self.isLeaf + u", fullUrl: " + self.fullUrl

