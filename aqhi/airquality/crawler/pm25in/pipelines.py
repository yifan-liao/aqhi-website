# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import os

from .items import PageItem
from aqhi.airquality import utils
from aqhi.airquality import models


class SavePagePipeline(object):
    def process_item(self, item, spider):
        logger = spider.custom_logger
        if isinstance(item, PageItem):
            city_name = item['name']
            page_content = item['page'].decode()
            # save record to database first
            try:
                info_dict = utils.extract_and_supplement(page_content, city_name)

                try:
                    create_status = models.create_city_record(info_dict)
                    record_info = '{name} on {dtm}'.format(name=city_name, dtm=info_dict['update_dtm'])
                    if create_status['success'] == 1:
                        logger.info('Successfully save a record: {}'.format(record_info))
                    else:
                        err_type = create_status['error_type']
                        if err_type == 'UniquenessError':
                            logger.warn('Ignore duplicate record: {}'.format(record_info))
                        else:
                            logger.error('Fail to save record: {record} because of {err_type}: {err_msg}'.format(
                                record=record_info,
                                err_type=err_type,
                                err_msg=create_status['info']
                            ))
                except Exception as e:
                    logger.error("Exception raised when saving record of city '{city}': {e}".format(
                        city=city_name,
                        e=repr(e)
                    ))

            except Exception as e:
                logger.error("Exception raised when parsing page of city '{city}': {e}".format(
                    city=city_name,
                    e=repr(e)
                ))
            finally:
                # backup file
                file_name = '{}.html'.format(city_name)
                with open(os.path.join(spider.res_dir, file_name), 'wb') as f:
                    f.write(item['page'])
                logger.info("Successfully backup the page of city '{}'".format(city_name))

