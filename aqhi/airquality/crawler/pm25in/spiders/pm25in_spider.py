# -*- coding: utf-8 -*-
import scrapy
import urllib.parse

from ..items import PageItem


class AQISpider(scrapy.Spider):
    name = 'pm25in_spider'
    allowed_domains = ['pm25.in']
    start_urls = [
        'http://pm25.in/',
    ]

    def __init__(self, res_dir, logger, page_num, to_parse=True, *args, **kwargs):
        super(AQISpider, self).__init__(*args, **kwargs)
        self.res_dir = res_dir
        self.custom_logger = logger
        self.page_num = page_num
        self.to_parse = to_parse

    def parse(self, response):
        # Get all city urls
        city_urls = response.xpath(
            "//div[contains(concat(' ', @class, ' '), ' all ')]//a/@href"
        ).extract()
        if self.page_num:
            city_urls = city_urls[:self.page_num]
        self.custom_logger.info('Get {} city urls.'.format(len(city_urls)))

        for url in city_urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_city_page)

    def parse_city_page(self, response):
        if response.status == 200:
            self.custom_logger.info('Successfully crawl from {}.'.format(response.url))
            yield PageItem(
                name=urllib.parse.urlparse(response.url).path[1:],
                page=response.body
            )
        else:
            self.custom_logger.warning()
            self.custom_logger.info('Fail to crawl from {}. Retry.'.format(response.url))
            yield scrapy.Request(response.url, callback=self.parse_city_page)


