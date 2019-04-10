import pickle
from typing import Union, List, Dict
import logging

import requests
from bs4 import BeautifulSoup
from selenium import webdriver

from helper import relate_path

logger = logging.getLogger(__name__)


class CarmaxBrowser:
    class CarmaxBrowserResponse(requests.Response):
        """
        Dummy class for static development
        """

        def __init__(self):
            super().__init__()
            # self.bs = BeautifulSoup()

    HOME_URL = 'https://www.carmax.com'

    default_headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        # 'Accept-Language': 'zh-CN,zh;q=0.9',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/70.0.3538.77 Mobile Safari/537.36 '
    }

    __requestsCookieJarKeys = ['version', 'name', 'value', 'port', 'domain', 'path', 'secure', 'expires', 'discard',
                               'comment',
                               'comment_url', 'rest', 'rfc2109']
    __seleniumCookieKeys = ['name', 'value', "path", "domain", "secure", "expiry"]

    def __init__(self, save_cookie='data/cookies'):
        self.driver = webdriver.Chrome(executable_path=relate_path(__file__, 'exec/chromedriver.exe'))
        self.save_cookie = save_cookie
        self.jar = requests.cookies.RequestsCookieJar()
        self.load_cookie()

    def load_cookie(self):
        self.driver.get(self.HOME_URL)
        try:
            cookies = pickle.load(open(self.save_cookie, 'rb'))
            [self.driver.add_cookie(i) for i in cookies]
            self.driver.get(self.HOME_URL)
        except Exception as e:
            pass

    def persistence_cookie(self):
        cookies = self.driver.get_cookies()
        if self.save_cookie:
            pickle.dump(cookies, open(self.save_cookie, 'wb'))
        # Convert selenium cookies into requests CookieJar
        for i, c in enumerate(cookies):
            _new = {}
            for k in c.keys():
                if k in CarmaxBrowser.__requestsCookieJarKeys:  # todo just use a map function here
                    _new[k] = c[k]
            cookies[i] = _new
        [self.jar.set(**i) for i in cookies]

    def get_body_html(self):
        return self.driver.execute_script('return document.body.innerHTML')

    def _set_cookies(self, cookies: Union[List, Dict]):
        raise NotImplemented()
        if type(cookies) is Dict:
            # todo self.jar.set( )
            pass

    def get(self, url):
        logger.debug('accessing "{}"'.format(url))
        self.driver.get(url)
        self.persistence_cookie()
        return self.driver.page_source

    def headless_get(self, url, params=None, **kwargs) -> CarmaxBrowserResponse:
        """Headless request
            Same as requests.get() arguments.

        :param url: URL for the new :class:`Request` object.
        :param params: (optional) Dictionary, list of tuples or bytes to send
            in the body of the :class:`Request`.
        :param kwargs: Optional arguments that ``request`` takes.
        :return: :class:`Response <Response>` object
        :rtype: GithubBrowserResponse
        """

        if 'cookies' in kwargs:
            raise NotImplemented()
            [self.jar.set(**i) for i in kwargs['cookies']]

        kwargs['cookies'] = self.jar

        if 'headers' in kwargs:
            kwargs['headers'] = dict(CarmaxBrowser.default_headers).update(kwargs['headers'])
        else:
            kwargs['headers'] = CarmaxBrowser.default_headers

        r = requests.get(url, params=params, **kwargs)

        # # Embedded a parsed bs node here
        # r.bs = BeautifulSoup(r.content, parser='html.parser')

        return r

    def close_browser(self):
        self.driver.close()
