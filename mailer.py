#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import smtplib
import socket
import sys
import json
import logging
from smtpd import COMMASPACE

import struct
from flask import request
from email.mime.text import MIMEText

from flask import Flask

app = Flask(__name__)


def load_config():
    """ 加载配置
    """
    config_path = sys.path[0] + os.sep + sys.argv[1]
    logger.info('加载配置 %s' % config_path)
    try:
        with open(config_path, 'rt') as config_file:
            config = json.loads(config_file.read())
            return config
    except IOError:
        logger.error('加载配置 %s 路径不对' % config_path)
        sys.exit(0)
    except Exception, e:
        logger.error('加载配置 %s 出错' % e.message)
        sys.exit(0)


def configure_logging(level):
    logger.setLevel(level)
    ch = logging.StreamHandler()
    ch.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s'
                                  ' - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)


def format_subnet(subnet_input):
    # 如果输入的ip，将掩码加上后输出
    if subnet_input.find("/") == -1:
        return subnet_input + "/255.255.255.255"
    else:
        # 如果输入的是短掩码，则转换为长掩码
        subnet = subnet_input.split("/")
        if len(subnet[1]) < 3:
            mask_num = int(subnet[1])
            last_mask_num = mask_num % 8
            last_mask_str = ""
            for i in range(last_mask_num):
                last_mask_str += "1"
            if len(last_mask_str) < 8:
                for i in range(8 - len(last_mask_str)):
                    last_mask_str += "0"
            last_mask_str = str(int(last_mask_str, 2))
            if mask_num / 8 == 0:
                subnet = subnet[0] + "/" + last_mask_str + "0.0.0"
            elif mask_num / 8 == 1:
                subnet = subnet[0] + "/255." + last_mask_str + ".0.0"
            elif mask_num / 8 == 2:
                subnet = subnet[0] + "/255.255." + last_mask_str + ".0"
            elif mask_num / 8 == 3:
                subnet = subnet[0] + "/255.255.255." + last_mask_str
            elif mask_num / 8 == 4:
                subnet = subnet[0] + "/255.255.255.255"
            subnet_input = subnet
            # 计算出正确的子网地址并输出
        subnet_array = subnet_input.split("/")
        subnet_true = socket.inet_ntoa(struct.pack("!I", struct.unpack("!I", socket.inet_aton(subnet_array[0]))[0] &
                                                   struct.unpack("!I", socket.inet_aton(subnet_array[1]))[0])) + "/" + subnet_array[1]
        return subnet_true

white_ip_list = []
subnet_white_array = []


def config_white_list(white_list):
    for white_ip in white_list:
        temp_ip = format_subnet(white_ip)
        white_ip_list.append(temp_ip)
        subnet_white_array.append(temp_ip.split("/")[1])


logger = logging.getLogger(__name__)
configure_logging(logging.ERROR)

config = load_config()
config_white_list(config['whiteList'])


@app.route('/')
def init():
    logger.error("IP come %s", request.remote_addr)
    if check_ip(request.remote_addr):
        return 'Hello Mailer!'
    else:
        return '500'


@app.route('/sendMail', methods=['POST'])
def send_mail():
    status_code = 500
    try:
        content = request.json
        smtp_send(config['smtp'], content)
        status_code = 200
    except Exception, e:
        logger.error('发送邮件出错,%s', e.message)
    return status_code


def smtp_send(smtp_config, m):
    from_email = smtp_config['username']
    if 'from' in m:
        from_email = m['from']
    msg = MIMEText(m['content'])
    msg['Subject'] = m['subject']
    msg['To'] = COMMASPACE.join(m['to'])
    msg['From'] = from_email
    s = smtplib.SMTP(smtp_config['host'], smtp_config['port'])
    if smtp_config['starttls']:
        s.starttls()
    s.login(smtp_config['username'], smtp_config['password'])
    s.sendmail(from_email, m['to'], msg.as_string())
    s.quit()


def check_ip(r_ip):
    for subnet in subnet_white_array:
        if format_subnet(r_ip + "/" + subnet) in white_ip_list:
            return True
    return False


if __name__ == '__main__':
    app.run(host=config['listen']['host'],
            port=config['listen']['port'],
            debug=False, use_reloader=False)
