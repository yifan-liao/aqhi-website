# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html
import scrapy


class PageItem(scrapy.Item):
    name = scrapy.Field()
    page = scrapy.Field()