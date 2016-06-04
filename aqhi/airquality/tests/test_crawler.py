# -*- coding: utf-8 -*-
from unittest import mock
import logging
import re

from django.test import SimpleTestCase, TestCase
from scrapy.http import Response, TextResponse

from aqhi.airquality.crawler.pm25in.spiders.pm25in_spider import AQISpider
from aqhi.airquality.crawler.pm25in.items import PageItem
from aqhi.airquality.crawler.pm25in.pipelines import SavePagePipeline
from . import factories


class AQISpiderTestCase(SimpleTestCase):
    def setUp(self):
        self.mock_logger = mock.create_autospec(logging.root)

    def test_parse(self):
        smaple_body = """<div class="all"><div class="top"> 全部城市：</div><div class="bottom"> <ul class="unstyled"> <div><b>A.</b></div><div> <li> <a href="/abazhou">阿坝州</a> </li><li> <a href="/akesudiqu">阿克苏地区</a> </li><li> <a href="/alashanmeng">阿拉善盟</a> </li><li> <a href="/aletaidiqu">阿勒泰地区</a> </li><li> <a href="/alidiqu">阿里地区</a> </li><li> <a href="/ankang">安康</a> </li><li> <a href="/anqing">安庆</a> </li><li> <a href="/anshan">鞍山</a> </li><li> <a href="/anshun">安顺</a> </li><li> <a href="/anyang">安阳</a> </li></div></ul></div></div>"""

        response = TextResponse('http://url', body=smaple_body, encoding='utf-8')
        spider = AQISpider('path', self.mock_logger, 0)
        request_it = spider.parse(response)
        self.assertEqual(
            [re.search(r'[a-z]+$', req.url, re.I).group() for req in request_it],
            ['abazhou', 'akesudiqu', 'alashanmeng', 'aletaidiqu', 'alidiqu', 'ankang', 'anqing', 'anshan', 'anshun', 'anyang']
        )

    def test_city_page(self):
        sample_body = b'abcd'

        response = Response('http://url/city1', body=sample_body)
        spider = AQISpider('path', self.mock_logger, 0)
        item_it = spider.parse_city_page(response)
        self.assertEqual(
            list(item_it),
            [PageItem(name='city1', page=sample_body)]
        )


class SavePagePipelineTestCase(TestCase):
    def setUp(self):
        self.mock_logger = mock.create_autospec(logging.root)

    @mock.patch('aqhi.airquality.crawler.pm25in.pipelines.open')
    @mock.patch('aqhi.airquality.utils.parse_and_create_records_from_html', autospec=True)
    def test_pipe(self, mock_parse_and_create, mock_open):
        info_dict = factories.InfoDictFactory()
        mock_parse_and_create.return_value = (info_dict, {'success': 1, 'info': factories.CityRecordFactory()})

        res_dir = 'path'
        item = PageItem(name='city', page=b'abcd')
        spider = AQISpider(res_dir, self.mock_logger, 0)

        SavePagePipeline().process_item(item, spider)
        mock_parse_and_create.assert_called_once_with('abcd', 'city')
        mock_open.assert_called_once_with('path/city.html', 'wb')
        self.assertEqual(self.mock_logger.info.call_count, 2)
        self.mock_logger.info.assert_any_call('Successfully save a record: {}'.format('{name} on {dtm}'.format(name='city', dtm=info_dict['update_dtm'])))
        self.mock_logger.info.assert_any_call("Successfully backup the page of city '{}'".format('city'))
