# -*- coding: utf-8 -*-

import re
import logging
import logging.config
from datetime import datetime

#logging.config.fileConfig('./logger.ini')
import scrapy
from scrapy.http import FormRequest,Request

from mbyr.items import FullPostItem,ImageItem
from mbyr.conf import ConfUtil
from mbyr.reduceRepetition import RepReducer

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

    repReducer = RepReducer()

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
                "id":ConfUtil.get_byr_account(),
                "passwd":ConfUtil.get_byr_pass(),
            }, callback = self.afterLogin,
        )
        return request


    def afterLogin(self,response):
        '''
        获得目录结构，记录到日志中，并开始爬取数据
        :param response:
        :return:
        '''
        logger = self.logger
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
    def inspect(self, response):
        from scrapy.shell import inspect_response
        inspect_response(response,self)

    def handle_li(self,li,isfirst):
        '''
        处理有内容的li标签
        可能需要处理图片与br 标签
        handle li tag
        tag contains username,posttime content user ip
        :param li:要处理的标签
        :param isfirst 是否是第一条信息
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
        imgItems = []
        div = li.css('.sp')
        if isfirst:
            content = div.extract()
            imgs = div.xpath('img')
            for img in imgs:
                imageItem = ImageItem()
                imageItem['href'] = img.xpath('@src').extract()[0]
                imageItem['done'] = False
                imgItems.append(imageItem)
        else:
            lines = div.xpath('text()').extract()
            content = u'\n'.join(lines)

        #暂时先不处理图片
        return (username,posttime,content,imgItems)

    def parseTop(self,response):
        '''
        处理第一页内容
        :param response:
        :return:
        '''
        stats = self.stats
        pageInfo = response.css('.plant')[-2].xpath('text()').extract()[0]
        (currPage,totalPage) = map(lambda x:int(x),pageInfo.split(u'/'))
        fullPostItem = FullPostItem()
        fullPostItem['name'] = response.meta['title']
        fullPostItem['type'] = 'top10'
        fullPostItem['url'] = response.url
        # 有热门评论的页面和没有热门评论的页面结构不一样，做如下区分，为了不让函数过多，所以两种情况都写在一个函数内
        hlb = response.css('.hlb')
        if len(hlb) != 0:
            # 有热门评论的页面
            stats.inc_value("top_ten_with_hot", 1, 0)
            # 首先处理热门评论和十大内容
            contents = response.css('.list')[0]
            # 获得十大相关内容
            li = contents.xpath('li')[1]
            username,posttime,content,imgItems = self.handle_li(li,True)
            for imgItem in imgItems:
                yield imgItem
            fullPostItem['time'] = posttime
            fullPostItem['user'] = username
            fullPostItem['content'] = content
            hots = []
            # 十大内容已经获得,接下来获得所有的热门评论
            div = contents.xpath('div')[1]
            li = div.xpath('li')
            tmp = {}
            tmp['user'] = li.xpath('div/a')[1].xpath('text()').extract()[0]
            tmp['vote'] = int(li.xpath('div/span/text()').extract()[0][2:-1])
            tmp['say'] = '\n'.join(li.xpath('div/text()').extract())
            hots.append(tmp)
            lis = div.css('#nicec').xpath('li')
            for item in lis:
                tmp = {}
                div = item.xpath('div')
                tmp['user'] = div[0].xpath('a')[1].xpath('text()').extract()[0]
                tmp['vote'] = int(div[0].xpath('span/text()').extract()[0][2:-1])
                tmp['say'] = '\n'.join(div[1].xpath('text()').extract())
                hots.append(tmp)
            fullPostItem['hots'] = hots
            lis = response.css('#m_main').xpath('li')
            fullPostItem['comments'] = [self.handle_li(li,False)[:-1] for index,li in enumerate(lis) if index not in (0,)]

            #from scrapy.shell import inspect_response
            #inspect_response(response,self)
            pass
        else:
            # 没有热门评论的页面
            stats.inc_value("top_ten_without_hot", 1, 0)
            contents = response.css('.list')
            if len(contents) != 0:
                self.logger.error(u".list 不是没有热门评论的选择器，结构可能被改变了")
                stats.inc_value('xpath_error',1,0)
            comments = contents[0].xpath('li')
            username,posttime,content,imgItems = self.handle_li(comments[1],True)
            #不管怎么样想yield
            for imgItem in imgItems:
                yield imgItem
            fullPostItem['time'] = posttime
            fullPostItem['user'] = username
            fullPostItem['content'] = content
            fullPostItem['comments'] = [
                self.handle_li(li,False)[:-1] for index,li in enumerate(comments) if index not in (0,1,2)
            ]
            #from scrapy.shell import inspect_response
            #inspect_response(response,self)
        # 如果还有下一页，则处理下一页内容
        if currPage < totalPage:
            yield Request(response.url + '?p=2', callback=self.parsnextpage,headers=self.headers,meta={
                'cookiejar':response.meta['cookiejar'],
                'fullpostitem' : fullPostItem,
                'currpage':2,
                'totalpage':totalPage
            })


    def parsnextpage(self,response):
        '''
        因为一个帖子不可能只有一页，所以用来处理接下来的页面
        :param response:
        :return:
        '''
        stats = self.stats
        fullpostitem = response.meta['fullpostitem']
        currpage = response.meta['currpage']
        totalpage = response.meta['totalpage']
        stats.inc_value("page%s"%currpage, 1, 0)
        lis = response.css('.list')[0].xpath('li')
        fullpostitem['comments'] = fullpostitem['comments'] + [
            self.handle_li(li, False)[:-1] for index, li in enumerate(lis) if index not in (0, 2)
        ]
        if currpage < totalpage:
            yield Request(response.url.split('?')[0] + '?p=%d'%(currpage+1), callback=self.parsnextpage,headers=self.headers,meta={
                'cookiejar':response.meta['cookiejar'],
                'fullpostitem' : fullpostitem,
                'currpage':currpage+1,
                'totalpage':totalpage
            })
        else:
            yield fullpostitem

    def parse(self, response):
        pass

    def getDirTree(self,response):
        nodes = response.css(".slist li")
        #from scrapy.shell import inspect_response
        #inspect_response(response,self)

        parent = response.meta['dirParent']
        stats = self.stats

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
                stats.inc_value("dir_count", 1, 0)
                tmpnode = DirNode(name, False, href)
                parent.appendChild(tmpnode)
                yield Request(tmpnode.fullUrl,callback=self.getDirTree,headers=self.headers,meta={
                    'cookiejar':response.meta['cookiejar'],
                    'dirParent':tmpnode
                })
            if(type.startswith(u"版面")):
                tmpnode = DirNode(name,True,href)
                parent.appendChild(tmpnode)
                stats.inc_value("board_count",1,0)
                # print(name)
                # print(href)
                # 开始处理版面
                # 十大信息已经全部处理完毕
                yield Request(
                    tmpnode.fullUrl, callback=self.parse_board, headers=self.headers, meta={
                        'cookiejar': response.meta['cookiejar'],
                        'name':name,
                        'type':href.split('/')[2]
                    }
                )

    def parse_board(self, response):
        '''
        处理board 的入口
        :param response:
        :return:
        '''
        stats = self.stats
        stype = response.meta['type']
        name = response.meta['name']
        # 增加board_1 计数
        stats.inc_value("board_1", 1, 0)
        # 增加获得类别页面数目的计数
        stats.inc_value("%s_board"%stype, 1, 0)
        ul = response.css('.list')
        lis = ul.xpath('li')
        # 记录board 当前是否已经完成遍历
        finished = False
        for li in lis:
            divs = li.xpath('div')
            top_div_a = divs[0].xpath('a')
            top_class = top_div_a.xpath('@class').extract()
            if len(top_class) and top_class[0] == 'top':
                # 热门帖子，处理热门
                top_url_hash = top_div_a.xpath('@href').extract()[0].split("/")[-1]
                if not self.repReducer.is_top_visited(name_space=stype, top_url_hash=top_url_hash):
                    stats.inc_value("unparse_top", 1, 0)
                    print u'热门帖子未被处理，但是我并不想处理，欢迎添加'
                    self.repReducer.visit_top(stype, top_url_hash)
            else:
                url_hash = top_div_a.xpath('@href').extract()[0].split("/")[-1]
                curr_index = int(divs[0].xpath('text()').extract()[0].rstrip(")").lstrip("("))
                last_crawl_index = self.repReducer.get_post_last_visit_index(name_space=stype,url_hash=url_hash)
                if last_crawl_index == curr_index:
                    finished = True
                    break
                else:
                    # 开始处理有未被爬取的帖子，有两类帖子，一类是完全没有被爬取的，另外一类是需要增量添加的帖子
                    if last_crawl_index == -1:
                        # 处理完全没有被爬取的帖子，和十大帖子处理逻辑一样
                        post_name = top_div_a.xpath("text()").extract()[0]
                        href = top_div_a.xpath("@href").extract()[0]
                        full_url = "http://m.byr.cn" + href
                        # 处理帖子的第一页
                        yield Request(
                            full_url, callback=self.parse_post_first_page, headers=self.headers,
                            meta={
                                'cookiejar':response.meta['cookiejar'],
                                'title':post_name,
                                'stype':stype,
                                'full_url':full_url
                            }
                        )
                        pass
                    else:
                        print u'需要处理部分内容被爬取的帖子'
                        pass

                    pass
                # 设置最先爬取到的位置
                self.repReducer.set_post_visit_index(name_space=stype,url_hash=url_hash,index=curr_index)

        if not finished:
            print u'页面遍历并未完成，访问下一页'

        pass

    def parse_post_first_page(self,response):
        print u'处理没有被爬取到的帖子'
        self.inspect(response)
        pass

class DirNode:

    def __init__(self,name,isLeaf,href):
        '''
        Consuturct
        :param name: ex. 笑口常开
        :param isLeaf: Is leaf node
        :param href: href, ex. /board/Joke
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


def handle_li(li,isfirst):
    '''
    处理有内容的li标签
    可能需要处理图片与br 标签
    handle li tag
    tag contains username,posttime content user ip
    :param li:要处理的标签
    :param isfirst 是否是第一条信息
    :return:
    '''
    from datetime import datetime
    from mbyr.items import ImageItem
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
    imgItems = []
    div = li.css('.sp')
    if isfirst:
        content = div.extract()
        imgs = div.xpath('img')
        for img in imgs:
            imageItem = ImageItem()
            imageItem['href'] = img.xpath('@src').extract()[0]
            imageItem['done'] = False
            imgItems.append(imageItem)
    else:
        lines = div.xpath('text()').extract()
        content = u'\n'.join(lines)

    #暂时先不处理图片
    return (username,posttime,content,imgItems)