#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import smtplib
import sys
import json
import logging
from smtpd import COMMASPACE

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

logger = logging.getLogger(__name__)
configure_logging(logging.ERROR)

config = load_config()


@app.route('/')
def init():
    logger.error("IP come %s", request.remote_addr)
    return 'Hello Mailer!'


@app.route('/sendMail', methods=['POST'])
def send_mail():
    status_code = 500
    try:
        content = request.json
        smtp_send(config['smtp'], content)
        status_code = 200
    except Exception, e:
        logger.error('发送邮件出错,%s', e.message)
    return 'send', status_code


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


if __name__ == '__main__':
    app.run(host=config['listen']['host'],
            port=config['listen']['port'],
            debug=False, use_reloader=False)
