import requests
import config
import sys


def Slack(*args):
    s = ' '.join(str(a) for a in args)
    if sys.platform.startswith('win'):
        s = '***DEV***\n' + s

    requests.post(
        url=config.SLACK_URL,
        json={'text': s}
    )
