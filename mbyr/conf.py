#coding=utf-8
__author__ = 'xiyuanbupt'
# e-mail : xywbupt@gmail.com

import ConfigParser
cf = ConfigParser.ConfigParser()
cf.read('global.ini')

class ConfUtil:

    @classmethod
    def get_byr_account(cls):
        return cf.get("byr","account")

    @classmethod
    def get_byr_pass(cls):
        return cf.get("byr","passw")

    @classmethod
    def get_redis_host(cls):
        return cf.get("redis","host")

    @classmethod
    def get_redis_port(cls):
        return cf.getint("redis", "port")

    @classmethod
    def get_redis_db(cls):
        return cf.getint("redis", "db")
