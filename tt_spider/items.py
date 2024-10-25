# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class TtItem(scrapy.Item):
    账号名 = scrapy.Field()
    url = scrapy.Field()
    播放 = scrapy.Field()
    点赞 = scrapy.Field()
    日期 = scrapy.Field()

    # id = scrapy.Field()
    # 发布时间 = scrapy.Field()
    # 昵称 = scrapy.Field()
    # 评论 = scrapy.Field()
    # 收藏 = scrapy.Field()
    # 分享 = scrapy.Field()
    备注 = scrapy.Field()

class TtSpiderItem(scrapy.Item):
    # define the fields for your item here like:
    name = scrapy.Field()
    title = scrapy.Field()
    info = scrapy.Field()
    pass
