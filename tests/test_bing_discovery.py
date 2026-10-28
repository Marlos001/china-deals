import base64
import unittest
from unittest.mock import patch
from china_deals import guest

class BingDiscoveryTests(unittest.TestCase):
    def test_bing_independent_provider_validates_urls_and_keeps_prices_unverified(self):
        target='https://item.jd.com/100214660452.html'
        encoded=base64.urlsafe_b64encode(target.encode()).decode().rstrip('=')
        body=f'<ol><li class="b_algo"><h2><a href="https://www.bing.com/ck/a?u=a1{encoded}">Audi wheel</a></h2><p>¥100</p></li></ol>'
        with patch.object(guest,'_fetch',return_value=(body,'https://www.bing.com/search?q=wheel')):
            result=guest.search_guest('jd','wheel',index_provider='bing')
        self.assertEqual(result['items'][0]['url'],target)
        self.assertIsNone(result['items'][0]['price'])
        self.assertEqual(result['items'][0]['source_mode'],'search_index')
    def test_bing_does_not_accept_unrelated_redirect_or_host(self):
        body='<li class="b_algo"><h2><a href="https://evil.test/123">bad</a></h2></li>'
        with patch.object(guest,'_fetch',return_value=(body,'https://www.bing.com/search')):
            result=guest.search_guest('jd','wheel',index_provider='bing')
        self.assertEqual(result['items'],[])
        self.assertEqual(result['status'],'empty_unverified')

    def test_challenge_gates_bing_without_automatic_retry(self):
        with guest.access_session(), patch.object(guest, '_fetch', return_value=('<title>Security check</title>', 'https://www.bing.com/search')) as fetch:
            first = guest.search_guest('jd', 'wheel', index_provider='bing')
            second = guest.search_guest('taobao', 'wheel', index_provider='bing')
        self.assertEqual(first['error']['code'], 'challenge')
        self.assertEqual(second['error']['code'], 'skipped_after_challenge')
        self.assertEqual(fetch.call_count, 1)

    def test_bing_rejects_ambiguous_or_malformed_encoded_target(self):
        for href in ('https://www.bing.com/ck/a?u=a1bad!','https://www.bing.com/ck/a?u=a1eA&u=a1eA'):
            self.assertEqual(guest._unwrap_bing(href), '')
