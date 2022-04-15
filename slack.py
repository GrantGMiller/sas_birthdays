import requests
import config
import sys

def Slack(*args):
    '''
    Send a Slack message to the admin.
    :param args: same as print()
    :return: None
    '''
    s = ' '.join(str(a) for a in args)
    if '127.0.0.1' in config.BASE_URL:
        s = '***DEV***\n' + s
    else:  # linux
        requests.post(
            url=config.SLACK_URL,
            json={'text': s}
        )
    print('Slack(s=', s)
