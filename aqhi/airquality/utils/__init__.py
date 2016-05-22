# -*- coding: utf-8 -*-
import math
import socket
import subprocess
from decimal import Decimal

import paramiko

from .. import models
from . import buptnet


def append_extra_fileds(info_dict):
    return append_aqhi_field(info_dict)


def calculate_aqhi(pm10, no2):
    return 10 / 16.4 * 100 * (math.exp(0.00019 * pm10) - 1 + math.exp(0.00061 * no2) - 1)


def calculate_aqhi_in_decimal(pm10_decimal, no2_decimal, prec=None):
    return Decimal(str(
        round(calculate_aqhi(float(pm10_decimal), float(no2_decimal)), prec)
    ))


def append_aqhi_field(info_dict):
    """
    Add aqhi value to the dict returned by extractors.process_parsed_dict.
    The precision is equal to the setting in models.

    :param info_dict: a dict full of info
    :return: the appended dict
    """
    prec = models.POLL_DECIMAL_PLACES
    for _, station_record in info_dict['stations'].items():
        station_record['aqhi'] = None
        pm10 = station_record['pm10']
        no2 = station_record['no2']
        if pm10 and no2:
            station_record['aqhi'] = calculate_aqhi_in_decimal(pm10, no2, prec)

    city_record = info_dict['city']
    city_record['aqhi'] = None
    pm10 = city_record['pm10']
    no2 = city_record['no2']
    if pm10 and no2:
        city_record['aqhi'] = calculate_aqhi_in_decimal(pm10, no2, prec)

    return info_dict


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
    cmd = 'find {} -type f -name "*.html" {}'.format(dir_path, city_pattern)

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