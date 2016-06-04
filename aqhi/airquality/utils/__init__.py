# -*- coding: utf-8 -*-
import math
import socket
import subprocess
from decimal import Decimal
from statistics import mean, StatisticsError

import paramiko

from .. import extractors
from .. import models
from . import buptnet


def parse_and_create_records_from_html(html_string, city_name_en):
    info_dict = extractors.process_parsed_dict(extractors.parse_info_dict(extractors.extract_info(html_string)))
    info_dict['city']['area_en'] = city_name_en
    create_status = models.create_city_record(info_dict)
    if create_status['success'] == 1:
        record = create_status['info']
        record.aqhi = record.calculate_aqhi_field()
        record.save()
    return info_dict, create_status


pollutant_coeffs = dict(
    no2=0.0004462559,
    so2=0.0001393235,
    o3=0.0005116328,
    pm10=0.0002821751,
    pm2_5=0.0002180567
)

ar_breakpoints = [
    1.88, 3.76, 5.64, 7.52, 9.41, 11.29, 12.91, 15.07, 17.22, 19.37, float('inf')
]


def calculate_pollutant_ar(avg_3h, coeff):
    return (math.exp(coeff * avg_3h) - 1) * 100


def calculate_aqhi(pm10_3h, pm25_3h, no2_3h, so2_3h, o3_3h):
    pm10_ar = calculate_pollutant_ar(pm10_3h, pollutant_coeffs['pm10'])
    pm25_ar = calculate_pollutant_ar(pm25_3h, pollutant_coeffs['pm2_5'])
    pm_ar = max(pm10_ar, pm25_ar)
    no2_ar = calculate_pollutant_ar(no2_3h, pollutant_coeffs['no2'])
    so2_ar = calculate_pollutant_ar(so2_3h, pollutant_coeffs['so2'])
    o3_ar = calculate_pollutant_ar(o3_3h, pollutant_coeffs['o3'])

    ar = no2_ar + so2_ar + o3_ar + pm_ar
    for i, breakpoint in enumerate(ar_breakpoints):
        if ar <= breakpoint:
            return i + 1


def calculate_aqhi_in_decimal(pm10_3h_dec, pm25_3h_dec, no2_3h_dec, so2_3h_dec, o3_3h_dec):
    return Decimal(calculate_aqhi(
        float(pm10_3h_dec), float(pm25_3h_dec), float(no2_3h_dec), float(so2_3h_dec), float(o3_3h_dec)
    ))


def get_ssh_client(hostname, username, password=None, port=22, timeout=5, log_file=None):
    """
    Use paramiko to create ssh session and return the ssh client.
    This will first try loading system host keys. If the loading fails, it will try to login with password
    again.
    Remember to call client.close() after you are done.

    :param hostname: ssh hostname
    :param username: ssh username
    :param password: ssh password
    :param port: ssh port
    :param timeout: connection timeout
    :param log_file: SSH log file. If this is not None, it must be in an existing directory.
    :return the ssh client
    :raise extractors.exception s
    """
    from aqhi.airquality.extractors import ssh_exception

    if log_file:
        paramiko.util.log_to_file(log_file)

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(hostname, port, username, password, timeout=timeout)
    except paramiko.ssh_exception.PasswordRequiredException:
        client.close()
        raise ssh_exception.PasswordRequiredException
    except paramiko.ssh_exception.AuthenticationException:
        client.close()
        raise ssh_exception.AuthenticationException
    except socket.timeout:
        client.close()
        raise ssh_exception.ConnectionTimeOut
    except socket.gaierror as e:
        client.close()
        if 'Name or service not known' in e.strerror:
            raise ssh_exception.ServerNotKnown
        else:
            raise e

    return client


def get_html_files_from_dir(dir_path, client=None, city_names=None):
    """
    Get all html files under `dir_path`, which is on local machine or remote one through ssh.

    :param dir_path: an existing root dir for searching html files
    :param client: an ssh client, optional.
    :type client: paramiko.SSHClient
    :param city_names: specific a list of cities to get, without path string
    :return: a generator yielding (file_name, file_content) pairs, with content as unicode string
    """
    city_pattern = ''
    if city_names is not None:
        city_pattern = '\\( -name "*{}.html" '.format(city_names[0])
        for city_name in city_names[1:]:
            city_pattern += '-o -name "*{}.html" '.format(city_name)
        city_pattern += '\\)'
    cmd = 'find {} -type f -name *.html {}'.format(dir_path, city_pattern)

    if client:
        sftp = client.open_sftp()

        file_name_it = (
            f.strip()
            for f in client.exec_command(cmd)[1]
        )
    else:
        file_name_it = (line for line in subprocess.check_output(cmd.split()).decode().strip().split('\n'))

    for file_name in file_name_it:
        if client:
            file = sftp.open(file_name)
        else:
            file = open(file_name, encoding='utf-8')

        content = file.read()
        if isinstance(content, bytes):
            content = content.decode(encoding='utf-8')
        yield file_name, content

        file.close()


def list_depth(l):
    """Count the max depth of a list."""
    if isinstance(l, list) and len(l) > 0:
        return 1 + max(list_depth(item) for item in l)
    else:
        return 0


def reduce_to_average_in_hours(city_records, hours=24, fields=None, default=None):
    """
    Give an iterable generating CityRecords with ascending datetime, return a list of records reduced to
    average record dicts of `days` days.

    Assume the interval is one hour. This function will not check the interval of the records.
    This will sort the records first by update_dtm with descending order.

    If there is any none value, it will be ignored when calculating average. Only if all values of a field is none,
    the field in the result is none.

    :param city_records: CityRecords iterable
    :param hours: designate how many hours of average, defaults to 24
    :param fields: a list or a single field name to count
        This defaults to models.DECIMAL_FIELDS, if one of the fields do not exist, exception will be raised
        Only selected fields will be included, but update_dtm will always be included.
    :param default: a function returning default value for None value, receiving record and field name as arguments
    :return: a list of averaged record dicts
    """
    if fields is None:
        fields = models.DECIMAL_FIELDS
    elif isinstance(fields, str):
        fields = [fields]
    fields = [f for f in fields if f in models.DECIMAL_FIELDS]

    res = []
    records = list(city_records)
    records.sort(key=lambda record: record.update_dtm, reverse=True)
    for record_chunk in (
            records[i:i + hours]
            for i in range(0, len(records), hours)
    ):
        if len(record_chunk) < hours:
            break
        reduced = reduce_to_one_record_dict(record_chunk, fields, True, default)
        reduced['update_dtm'] = record_chunk[0].update_dtm
        res.append(reduced)

    return res


def reduce_to_one_record_dict(city_records, fields, _round=True, default=None):
    res = {}

    for field in fields:

        values = []
        for rec in city_records:
            value = getattr(rec, field)
            if value is None:
                if default is not None:
                    value = default(rec, field)
                    if value is not None:
                        values.append(value)
            else:
                values.append(value)

        if len(values) == 0:
            res[field] = None
        else:
            mean_value = mean(values)
            res[field] = round(mean_value, models.POLL_DECIMAL_PLACES) if _round else mean_value

    return res
