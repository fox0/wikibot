import logging
import requests

from private_settings import USERNAME, PASSWORD

log = logging.getLogger(__name__)


class WikiAPI:
    headers = {
        'user-agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:73.0) Gecko/20100101 Firefox/73.0',
    }
    url = 'https://ru.wikipedia.org/w/api.php'

    # https://ru.wikipedia.org/w/rest.php

    def __init__(self):
        self.s = requests.Session()

    def login(self):
        login_token = self.get_login_token()
        # As of MediaWiki 1.27, using the main account for login is not supported.
        # Obtain credentials via Special:BotPasswords or use clientlogin method.
        r = self._post({
            'action': 'clientlogin',
            'username': USERNAME,
            'password': PASSWORD,
            'loginreturnurl': 'http://127.0.0.1:5000/',
            # At least one of the parameters "logincontinue" and "loginreturnurl" is required.
            'logintoken': login_token,
        })
        # log.debug(r)
        if r['clientlogin']['status'] != 'PASS':
            raise ValueError(r)

    def get_login_token(self):
        """токен одноразовый"""
        r = self._get({'action': 'query', 'meta': 'tokens', 'type': 'login'})
        token = r['query']['tokens']['logintoken']
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
        lastrevid = page['lastrevid']
        stable_revid = page['flagged']['stable_revid']
        return lastrevid == stable_revid

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


def main():
    title = 'Jive_Records'

    api = WikiAPI()
    api.login()

    print(api.is_stable(title))

    # print(api.get_page(title))
    api.get_token()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
