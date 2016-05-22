# -*- coding: utf-8 -*-
import requests
import lxml.html
import re
import requests.exceptions
from urllib.parse import urlparse
import argparse
import sys
import os
import configparser

url = 'http://gw.bupt.edu.cn'
logout_url = 'http://gw.bupt.edu.cn/F.html'

_messages = {
    'CommandLine': {
        'SettingFileNotExist': '{file} file does not exist.',
        'NoAuthSecInSettingFile': '{file} file lacks AUTH section.',
        'NoUnameOrPasswdInSettingFile': '{file} file lack Username or Password key in AUTH section',
        'SilentOptionNotWithSubcmd': 'silent option cannot be used with any subcommand.',
        'LogOutSuccess': 'Log out successfully',
        'LogInSuccess': 'Log in successfully. \nUsed time: {used_time} \n'
                        'Used internet traffic: {used_internet_traffic} \nBalance: {balance} \n'
    },
    'Network': {
        'in': 'You have already logged in.',
        'out': 'You have already logged out.',
        'offline': 'Internet is not reachable.',
        'out_of_network': 'Campus network is not reachable.',
    }
}


def _extract_account_info(parsed_page):
    """
    Extract account info from a page parsed by lxml.html.fromstring

    :param parsed_page: the object returned by `lxml.html.fromstring` or `lxml.html.parse(file_path).getroot()`
    :return: a list of `dict`s containing the info with fields: `name`, `value`, `unit`
    """
    js_code = parsed_page.xpath(
        "//head/script/text()"
    )[0]

    pattern_number = '[-+]?[0-9]*\\.?[0-9]+'

    info = []
    # Get used time
    time = re.search(
        "time\\s*=\\s*'\\s*(" + pattern_number + ")\\s*'", js_code
    ).group(1)
    info.append(dict(name='used_time', value=time, unit='Min'))

    # Get used traffic
    flow = int(re.search(
        "flow\\s*=\\s*'\\s*(" + pattern_number + ")\\s*'", js_code
    ).group(1))
    flow0 = flow % 1024
    flow1 = flow - flow0
    flow0 *= 1000
    flow0 -= flow0 % 1024
    flow3 = '.'
    if flow0 / 1024 < 10:
        flow3 = '.00'
    elif flow0 / 1024 < 100:
        flow3 = '.0'
    traffic = str(int(flow1 / 1024)) + flow3 + str(int(flow0 / 1024))
    info.append(dict(name='used_internet_traffic', value=traffic, unit='MByte'))

    # Get fee
    fee = int(re.search(
        "fee\\s*=\\s*'\\s*(" + pattern_number + ")\\s*'", js_code
    ).group(1))
    fee = str((fee - fee % 100) / 10000)
    info.append(dict(name='balance', value=fee, unit='RMB'))

    return info


def _extract_resp_page_info(parsed_page):
    """
    Extract info from the response page.
    Return a `dict` to show whether the page says success or failure.
    This `dict` contains a `success` flag, a `type` indicating the success/failure type and a `message`.
    - When it is a success, `success` flag will be set to `1` and `type` will be one of the following:
      {'Logout', 'Login'}
    - When it is a failure, `success` flag is `0` and `type` is one of:
      {'AuthError', 'MaxConnection', 'AccountOverspent', 'AccountSuspended', 'UnknownError'}

    :param parsed_page: the object returned by `lxml.html.fromstring` or `lxml.html.parse(file_path).getroot()`
    :return: a `dict` indicating the response page state
    """
    js_code = parsed_page.xpath("//head/script/text()")[0]

    msg_match = re.search(
        "Msg\\s*=\\s*([-+]?[0-9]*\\.?[0-9]+)", js_code
    )

    if msg_match:
        # Condition #1: Login fail and logout success page
        msg = int(msg_match.group(1))
        msga = re.search(
            "msga\\s*=\\s*'\\s*(.*?)\\s*'", js_code
        ).group(1)

        if msg in [0, 1]:
            if msg == 1 and msga != "":
                if msga == 'ldap auth error':
                    return dict(success=0, type='AuthError', message='Invalid account or password.')
            else:
                return dict(success=0, type='AuthError', message='Invalid account or password.')
        elif msg == 2:
            return dict(success=0, type='MaxConnection', message='Reach max number of logged-in IPs.')
        elif msg == 4:
            return dict(success=0, type='AccountOverspent', message='This account overspent or over time limit.')
        elif msg == 5:
            return dict(success=0, type='AccountSuspended', message='This account has been suspended.')
        elif msg == 14:
            return dict(success=1, type='Logout', message='Logout successfully.')
        elif msg == 15:
            return dict(success=1, type='Login', message='Login successfully.')

        return dict(success=0, type='UnknownError', message='UNKNOWN RESPONSE (msg={}, msga={})'.format(msg, msga))

    else:
        # Condition #2: Login success page
        success_prompt = parsed_page.xpath(
            "//div[contains(concat(' ', @class, ' '), ' b_cernet ')]//tr/td"
        )[1].text_content()
        if 'successfully logged' in success_prompt:
            return dict(success=1, type='Login', message='Login successfully.')

    return dict(success=0, type='UnknownError', message='UNKNOWN RESPONSE')


def login(username, password, url=None):
    """
    Attempt to login to BUPT network using `username` and `password`.
    Login URL defaults to 'http://gw.bupt.edu.cn'.
    Return a `dict` with attempt results:
    - Success: {'success': 1, 'info': [{'name': 'used_time', 'value': '4000', unit: 'min'}, ... ]
    - Failure: {'success': 0, 'info': {'type': 'ConnectionError', 'message': '...')
    Error's `type` can be one of:
    {'InternetNotReachable', 'AlreadyLoggedIn', 'NotInCampus', 'ConnectionError', 'UnknownError'}
    plus those returned by `_extract_resp_page_info()`.

    :param username: login username, usually it's your student id
    :param password: login password, plain string
    :param url: login page's URL.
    :return: a `namedtuple` indicating
    """
    network_messages = _messages['Network']
    if url is None:
        url = globals()['url']

    # Check network status first
    try:
        res = check_network_status(url)
    except requests.exceptions.RequestException as e:
        return dict(success=0, info=dict(type=e.__class__.__name__, message=str(e)))

    status = res['status']
    if status == 'offline':
        return dict(success=0, info=dict(type='InternetNotReachable', message=network_messages['out']))
    elif status == 'in':
        return dict(success=0, info=dict(type='AlreadyLoggedIn', message=network_messages['in']))
    elif status == 'out_of_network':
        return dict(success=0, info=dict(type='NotInCampus', message=network_messages['out_of_network']))

    # Try to log in
    try:
        resp = requests.post(
            url,
            {
                'DDDDD': username,
                'upass': password,
                'AMKKey': '',
            },
        )
    except requests.RequestException as e:
        return dict(success=0, info=dict(type=e.__class__.__name__, message=str(e)))

    resp_page_roote = lxml.html.fromstring(resp.text)
    resp_info = _extract_resp_page_info(resp_page_roote)
    success_flag = resp_info['success']
    if success_flag:
        if resp_info['type'] == 'Login':
            # After logging in successfully, access the url again and get account info
            try:
                resp = requests.get(url, timeout=3)
            except requests.RequestException as e:
                return dict(success=0, info=dict(type=e.__class__.__name__, message=str(e)))

            return dict(success=1, info=_extract_account_info(lxml.html.fromstring(resp.text)))
        else:
            return dict(
                success=0,
                info=dict(
                    type='UnknownError', message='Successfully done another thing when trying to log in.'
                )
            )
    else:
        return dict(success=0, info=dict(type=resp_info['type'], message=resp_info['message']))


def logout(logout_url=None, url=None):
    """
    Attempt to log out campus network.
    Return a `dict` showing whether logging out successfully or not
    - Successfully: {'success': 1}
    - Otherwise: {'success': 0, 'info': {'type': '...', 'message': '...'}

    :param logout_url: log-out URL. This defaults to 'http://gw.bupt.edu.cn/F.html'
    :param url: main URL.
    :return: a `dict` showing success or failure
    """
    network_messages = _messages['Network']

    if logout_url is None:
        logout_url = globals()['logout_url']

    if url is None:
        url = globals()['url']

    # Check network status first
    try:
        res = check_network_status(url)
    except requests.exceptions.RequestException as e:
        return dict(success=0, info=dict(type=e.__class__.__name__, message=str(e)))

    status = res['status']
    if status == 'offline':
        return dict(success=0, info=dict(type='InternetNotReachable', message=network_messages['offline']))
    elif status == 'out':
        return dict(success=0, info=dict(type='AlreadyLoggedOut', message=network_messages['out']))
    elif status == 'out_of_network':
        return dict(success=0, info=dict(type='NotInCampus', message=network_messages['out_of_network']))

    # Try to log out
    try:
        resp = requests.get(logout_url)
    except requests.RequestException as e:
        return dict(success=0, info=dict(type=e.__class__.__name__, message=str(e)))

    resp_page_roote = lxml.html.fromstring(resp.text)
    resp_info = _extract_resp_page_info(resp_page_roote)
    success_flag = resp_info['success']
    if success_flag:
        if resp_info['type'] == 'Logout':
            return dict(success=1)
        else:
            return dict(
                success=0,
                info=dict(
                    type='UnknownError', message='Successfully done another thing when trying to log out.'
                )
            )
    else:
        return dict(success=0, info=dict(type=resp_info['type'], message=resp_info['message']))


def check_network_status(url=None):
    """
    Check if it is logged in and return different info:
    1. return `{'status': 'in', 'info': {...} } # with account info
    2. return `{'status': 'offline'}` if offline or unable to log in
    3. return `{'status': 'out'}` if online and able to log in
    4. return `{'status': 'out_of_network'}` if online but outside school

    Throw request exceptions except for ConnectionError.

    :param url: the URL to check the state, defaults to 'http://gw.bupt.edu.cn'
    :return: a `dict` containing network status and info
    """
    if url is None:
        url = globals()['url']

    # Check if offline
    try:
        resp = requests.get('http://baidu.com', timeout=3)
    except requests.ConnectionError:
        try:
            resp = requests.get('https://google.com', timeout=3)
        except requests.ConnectionError:
            return dict(status='offline')

    # Check if able to log in
    parts = urlparse(resp.url)
    if re.match(r'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+', parts.netloc):
        # redirect to log in page
        return dict(status='out')

    # Check if you can reach the log in page
    try:
        resp = requests.get(url, timeout=3)
    except requests.ConnectionError:
        return dict(status='out_of_network')

    return dict(
        status='in',
        info=_extract_account_info(lxml.html.fromstring(resp.text))
    )


def query_yes_no(question, default="yes"):
    """
    Ask a yes/no question via input() and return their answer.

    :param question: a string that is presented to the user
    :param default: the presumed answer if the user just hits <Enter>.
                    It must be "yes" (the default), "no" or None (meaning
                    an answer is required of the user)
    :return: True for "yes" or False for "no"
    """
    valid = {"yes": True, "y": True,
             "no": False, "n": False}
    if default is None:
        prompt = " (y/n) "
    elif default == "yes":
        prompt = " ([y]/n) "
    elif default == "no":
        prompt = " (y/[n]) "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        print(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            print("Please respond with 'yes' or 'no' "
                  "(or 'y' or 'n').\n")


def autologin(username, password, logger, url=url):
    status_dict = check_network_status(url)
    status = status_dict['status']
    if not status == 'in':
        logger.info('Internet is not reachable.')
        if status == 'out':
            logger.info('Try to log into campus network.')
            login_res = login(username, password, url)
            success = login_res['success']
            if success:
                logger.info('Log in successfully.')
                return True
            else:
                logger.error('Can not log in: {}: {}. Abort.'.format(
                    login_res['info']['type'], login_res['info']['message']
                ))
                return False
        else:
            logger.error('Not in campus network. Can not reach gateway. Abort.')
            return False


default_setting_file = '.buptnet'


def parse_args(args):
    cmd_messages = _messages['CommandLine']
    network_messages = _messages['Network']

    parser = argparse.ArgumentParser(
        prog='buptnet',
        description='Log in, log out BUPT campus network and check the status of the net.',
    )
    parser.add_argument('-s', '--silent', action='store_true',
                        help='Silently log in or out according to present status.')
    subparsers = parser.add_subparsers()

    parser_login = subparsers.add_parser('login')
    parser_logout = subparsers.add_parser('logout')
    parser_status = subparsers.add_parser('status')

    options = vars(parser.parse_args(args))
    silent = options.get('silent')
    if not('login' in args or 'logout' in args or 'status' in args):
        # Call without subcommands
        # First read conf file
        if not os.path.exists(default_setting_file):
            parser.error(cmd_messages['SettingFileNotExist'].format(file=default_setting_file))

        with open(default_setting_file) as conf_file:
            config = configparser.ConfigParser()
            config.read_file(conf_file)

            if not('AUTH' in config.sections()):
                parser.error(cmd_messages['NoAuthSecInSettingFile'].format(file=default_setting_file))

            username = config.get('AUTH', 'Username', fallback=None)
            password = config.get('AUTH', 'Password', fallback=None)
            if not(username and password):
                parser.error(cmd_messages['NoUnameOrPasswdInSettingFile'].format(file=default_setting_file))

            main_url = config.get('DEFAULT', 'MainURL', fallback=None) or globals()['url']
            logout_url = config.get('DEFAULT', 'LogOutURL', fallback=None) or globals()['logout_url']

            try:
                status_dict = check_network_status(main_url)
            except requests.RequestException as e:
                parser.error('{}: {}'.format(e.__class__.__name__, str(e)))

            status = status_dict['status']
            if status == 'offline':
                parser.error(network_messages['offline'])
            elif status == 'out_of_network':
                parser.error(network_messages['out_of_network'])
            elif status == 'in':
                try:
                    if silent or query_yes_no('You have logged in. Do you want to log out?', default='no'):
                        res = logout(logout_url, main_url)
                        if res['success']:
                            parser.exit(message=cmd_messages['LogOutSuccess'])
                        else:
                            parser.error('{}: {}'.format(res['info']['type'], res['info']['message']))
                except (KeyboardInterrupt, EOFError):
                    parser.exit()
                parser.exit()
            elif status == 'out':
                try:
                    if silent or query_yes_no('You have logged out. Do you want to log in?', default='no'):
                        res = login(username, password, main_url)
                        if res['success']:
                            for info_dict in res['info']:
                                if info_dict['name'] == 'used_time':
                                    used_time = "{value} {unit}".format(**info_dict)
                                elif info_dict['name'] == 'used_internet_traffic':
                                    used_internet_traffic = "{value} {unit}".format(**info_dict)
                                elif info_dict['name'] == 'balance':
                                    balance = "{value} {unit}".format(**info_dict)
                            parser.exit(message=cmd_messages['LogInSuccess'].format(
                                used_time=used_time, used_internet_traffic=used_internet_traffic, balance=balance))
                        else:
                            parser.error('{}: {}'.format(res['info']['type'], res['info']['message']))
                except (KeyboardInterrupt, EOFError):
                    parser.exit()
                parser.exit()
    else:
        if silent:
            parser.error(cmd_messages['SilentOptionNotWithSubcmd'])


if __name__ == '__main__':
    parse_args(sys.argv[1:])
