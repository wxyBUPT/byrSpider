#coding=utf-8
__author__ = 'xiyuanbupt'
# e-mail : xywbupt@gmail.com

import string
import json

import requests

class UrlGenerator:

    wiki_base = "https://en.wikipedia.org/wiki/"
    api_url = "https://en.wikipedia.org/w/api.php"
    querystring = {
        "action":"query",
        "list":"allpages",

        "apfrom":"A",
        "apto":"Ab",

        "aplimit":"100",
        "format":"json",
        "apfilterredir":"nonredirects",
        "apminsize":"4000"
    }

    def __init__(self):

        self.end = "a"
        self.urls = []
        self.tags = []
        for s in string.ascii_uppercase:
            for k in string.ascii_lowercase:
                for j in string.ascii_lowercase:
                    self.tags.append(s + k + j)

    def get_next(self):
        if len(self.urls) != 0:
            name = self.urls.pop()
            return self.wiki_base + name,name
        else:
            while len(self.urls) == 0:
                apfrom = self.tags.pop()
                apto = apfrom + 'z'
                self.querystring['apfrom'] = apfrom
                self.querystring['apto'] = apto
                res = requests.request("GET",self.api_url,params = self.querystring)
                json_str = res.content
                allpages = json.loads(json_str)
                self.urls = [item['title'] for item in allpages['query']['allpages']]
            name = self.urls.pop()
            return self.wiki_base + name, name
