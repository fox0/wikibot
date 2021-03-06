import time
import random
import logging
import subprocess
import requests
from private_settings import USERNAME, PASSWORD

log = logging.getLogger(__name__)


class WikiAPI:
    headers = {
        'user-agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:73.0) Gecko/20100101 Firefox/73.0',
    }
    url = 'https://ru.wikipedia.org/w/api.php'

    def __init__(self):
        self.s = requests.Session()

    def login(self, username, password):
        login_token = self.get_login_token()
        # As of MediaWiki 1.27, using the main account for login is not supported.
        # Obtain credentials via Special:BotPasswords or use clientlogin method.
        r = self._post({
            'action': 'clientlogin',
            'username': username,
            'password': password,
            'loginreturnurl': 'http://127.0.0.1:5000/',
            # At least one of the parameters "logincontinue" and "loginreturnurl" is required.
            'logintoken': login_token,
        })
        # log.debug(r)
        if r['clientlogin']['status'] != 'PASS':
            raise ValueError(r)

    def patrol(self, rcid):
        # 'code': 'patroldisabled', 'info': 'Recent changes patrol disabled
        token = self.get_patrol_token()
        r = self._post({
            'action': 'patrol',
            'token': token,
            'revid': rcid,
        })
        return r

    def get_login_token(self):
        """токен одноразовый"""
        r = self._get({'action': 'query', 'meta': 'tokens', 'type': 'login'})
        token = r['query']['tokens']['logintoken']
        # log.debug(token)
        return token

    def get_patrol_token(self):
        r = self._get({'action': 'query', 'meta': 'tokens', 'type': 'patrol'})
        token = r['query']['tokens']['patroltoken']
        # log.debug(token)
        return token

    def get_token(self):
        r = self._get({'action': 'query', 'meta': 'tokens'})
        token = r['query']['tokens']['csrftoken']
        # log.debug(token)
        return token

    def get_page(self, title):
        r = self._get({'action': 'parse', 'page': title, 'prop': 'wikitext'})
        return r['parse']['wikitext']['*']

    def is_stable(self, title):
        r = self._get({'action': 'query', 'prop': 'info|flagged', 'titles': title})
        page = list(r['query']['pages'].values())[0]
        try:
            lastrevid = page['lastrevid']
        except KeyError:  # deleted
            return True
        try:
            stable_revid = page['flagged']['stable_revid']
        except KeyError:
            return False
        return lastrevid == stable_revid

    def save_page(self, title, text, summary):
        token = self.get_token()
        r = self._post({
            'action': 'edit',
            'minor': True,
            'title': title,
            'text': text,
            'summary': summary,
            'token': token,
        })
        return r

    def _get(self, params):
        return self._request('GET', params=params)

    def _post(self, data):
        return self._request('POST', data=data)

    def _request(self, method, params=None, data=None):
        if params is not None:
            params['format'] = 'json'
        else:
            data['format'] = 'json'
        return self.s.request(method, self.url, headers=self.headers, params=params, data=data).json()


def run(api, title):
    # if api.is_stable(title):
    #     log.warning('is_stable')
    #     return False

    try:
        text = api.get_page(title)
    except KeyError:
        return False
    p = subprocess.run(('js', 'wikificator.js'), stdout=subprocess.PIPE, input=text, encoding='utf-8')
    text2 = p.stdout
    if text2 == text:
        log.warning('==')
        return True

    r = api.save_page(title, text2, '[[ПРО:CW|Checkwiki]] #1. Исправление избыточного префикса "Шаблон:"')
    # return api.save_page(title, text2, '[[ПРО:CW|Checkwiki]] #64. Исправление внутренних ссылок')
    try:
        return r['edit']['result'] == 'Success'
    except KeyError:
        return False


def main():
    api = WikiAPI()
    api.login(USERNAME, PASSWORD)

    # todo https://tools.wmflabs.org/checkwiki/cgi-bin/checkwiki.cgi?project=ruwiki&view=bots&id=64&offset=0
    with open('1.txt') as f:
        ls = f.readlines()
        i = 0
        m = 250
        while i < m:
            title = random.choice(ls).strip()
            log.info(title)
            if run(api, title):
                requests.get('https://tools.wmflabs.org/checkwiki/cgi-bin/checkwiki.cgi', params={
                    'project': 'ruwiki', 'view': 'only', 'id': 1, 'title': title})
                log.debug('%d of %d, Sleep...', i, m)
                time.sleep(10)
                i += 1


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
