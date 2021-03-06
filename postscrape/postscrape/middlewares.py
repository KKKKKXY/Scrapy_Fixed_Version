from itemadapter import is_item, ItemAdapter
import time
import os.path
import requests
import pickle
import os
from scrapy import signals
from scrapy.http import HtmlResponse
from requests.exceptions import Timeout
from scrapy.downloadermiddlewares.retry import RetryMiddleware
import logging
import scrapy
import json


class PostscrapeSpiderMiddleware(object):

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        return None

    def process_spider_output(self, response, result, spider):
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        pass

    def process_start_requests(self, start_requests, spider):
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class PostscrapeDownloaderMiddleware(RetryMiddleware):
    def __init__(self):
        self.success_count = 0
        self.fail_count    = 0
        self.max_retry_times = 2
        self.priority_adjust =  -39

    def __del__(self):
        print("Downloader(finished): finish scraping, Totally %d companys, %d data completed, %d data failed==========" %(self.success_count + self.fail_count, self.success_count, self.fail_count))

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        #load cookie from local
        cookie_path = '/Users/mya/Desktop/Development/scrapyTest/postscrape/postscrape/spiders/temp/cookie.json'
        if os.path.isfile(cookie_path):
            try:
                with open(cookie_path, 'rb') as f: 
                    cookies = pickle.load(f)
            except EOFError:
                cookies = None

        for i in cookies:
            if i['name']=='JSESSIONID':
                cookies= i['value']
                break

        try:
            #time.sleep(0.1)
            # response = scrapy.Request(request.url, cookies={"JSESSIONID":cookies})
            response = requests.get(request.url, cookies = {'JSESSIONID':cookies}, timeout=60, verify=False)
            html = str(response.content,'utf-8')
            page =  html
            scrapy_response = HtmlResponse(url=request.url, body=page, request=request, encoding='utf-8')
            scrapy_response.status_code = response.status_code

        except Timeout:
            print('Get page time out!')
            self.fail_count += 1
            request.status = False
            scrapy_response = HtmlResponse(url=request.url, body='', request=request, encoding='utf-8')
            scrapy_response.status_code = 'timeout'
            return scrapy_response

        return scrapy_response

    def process_response(self, request, response, spider):
        code = response.status_code


        if code == 404:
            #if the company cannot be found
            print(f'Downloader: cannot find the page in datawarehouse {response.url}')
            request.status = False
            self.fail_count += 1

        elif code == 200:
            #find the search bar
            search_bar = response.xpath('/html/body/div/div[4]/div[1]')
            if search_bar:
                # if search bar exist but the name is not exist. the company is not exist
                check = response.xpath('/html/body/div/div[4]/div[2]/div[1]/div[2]/div[2]/div[2]/div/div/h2/text()')
                if not check:
                    request.status = False
                    self.fail_count += 1
                else:
                    request.status = True
                    self.success_count += 1
            else:
                print(f'time out {request.url}')
                request.status = False
                return self._retry(request, response, spider) or response

        elif code == 'timeout':
            print(f'time out {request.url}')
            request.status = False
            return self._retry(request, response, spider) or response

        elif code == 401:
            #if cookie died
            #raise CloseSpider('@@@@@@@@@@@@@@@the cooike expired in scraping@@@@@@@@@@@@@@@@')
            print('Downloader: cookie expired!')
            spider.close_it = 'cookie expired!'
        elif  code == 500 or code == 503:
            #if the server down:500, 503
            #or some error system does not know: 000

            #self.fake_browser.driver.save_screenshot('failed.png')
            #raise CloseSpider('@@@@@@@@@@@@@@@@@@@@the server is down! Please try to run it later@@@@@@@@@@@@@@@@@')
            print(f'Downloader: server is down! code{code}')
            spider.close_it = f'server is down! code{code}'
        else:
            print(f'Downloader: unexpect error! code {code}')
            spider.close_it = f'unexpect error! code{code}'



        return response

    def process_exception(self, request, exception, spider):
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)



# import time
# import os.path
# import requests
# import pickle
# import os
# from scrapy import signals
# from scrapy.http import HtmlResponse
# from requests.exceptions import Timeout
# from scrapy.downloadermiddlewares.retry import RetryMiddleware
# from itemadapter import is_item, ItemAdapter


# class PostscrapeSpiderMiddleware(object):

#     @classmethod
#     def from_crawler(cls, crawler):
#         s = cls()
#         crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
#         return s

#     def process_spider_input(self, response, spider):

#         return None

#     def process_spider_output(self, response, result, spider):
#         # Called with the results returned from the Spider, after
#         # it has processed the response.

#         # Must return an iterable of Request, or item objects.
#         for i in result:
#             yield i

#     def process_spider_exception(self, response, exception, spider):
#         # Called when a spider or process_spider_input() method
#         # (from other spider middleware) raises an exception.

#         # Should return either None or an iterable of Request or item objects.
#         pass

#     def process_start_requests(self, start_requests, spider):
#         # Called with the start requests of the spider, and works
#         # similarly to the process_spider_output() method, except
#         # that it doesn’t have a response associated.

#         # Must return only requests (not items).
#         for r in start_requests:
#             yield r

#     def spider_opened(self, spider):
#         spider.logger.info('Spider opened: %s' % spider.name)


# class PostscrapeDownloaderMiddleware(RetryMiddleware):
#     @classmethod
#     def from_crawler(cls, crawler):
#         s = cls()
#         crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
#         return s

#     def process_request(self, request, spider):
#         #load cookie from local
#         cookie_path = '/Users/mya/Desktop/Development/scrapyTest/postscrape/postscrape/spiders/temp/cookie.json'
#         if os.path.isfile(cookie_path):
#             try:
#                 with open(cookie_path, 'rb') as f: 
#                     cookies = pickle.load(f)
#             except EOFError:
#                 cookies = None

#         for i in cookies:
#             if i['name']=='JSESSIONID':
#                 cookies= i['value']
#                 break

#         try:
#             response = requests.get(request.url, cookies = {'JSESSIONID':cookies}, timeout=10)
#             html = str(response.content,'utf-8')
#             page =  html
#             scrapy_response = HtmlResponse(url=request.url, body=page, request=request, encoding='utf-8')
#             scrapy_response.status_code = response.status_code

#         except Timeout:
#             print('Get page time out!')
#             request.status = False
#             scrapy_response = HtmlResponse(url=request.url, body='', request=request, encoding='utf-8')
#             scrapy_response.status_code = 'timeout'
#             return scrapy_response

#         return scrapy_response

#     def process_response(self, request, response, spider):
#         code = response.status_code

#         if code == 404:
#             #if the company cannot be found
#             print(f'Downloader: cannot find the page in datawarehouse {response.url}')
#             request.status = False

#         # elif code == 200:
#         #     #find the search bar
#         #     search_bar = response.xpath('/html/body/div/div[4]/div[1]')
#         #     if search_bar:
#         #         # if search bar exist but the name is not exist. the company is not exist
#         #         check = response.xpath('/html/body/div/div[4]/div[2]/div[1]/div[2]/div[2]/div[2]/div/div/h2/text()')
#         #         if not check:
#         #             request.status = False
#         #         else:
#         #             request.status = True
#         #     else:
#         #         print(f'time out {request.url}')
#         #         request.status = False
#         #         return self._retry(request, response, spider) or response

#         elif code == 'timeout':
#             print(f'time out {request.url}')
#             request.status = False
#             return self._retry(request, response, spider) or response

#         elif code == 401:
#             #if cookie died
#             #raise CloseSpider('@@@@@@@@@@@@@@@the cooike expired in scraping@@@@@@@@@@@@@@@@')
#             print('Downloader: cookie expired!')
#             spider.close_it = 'cookie expired!'
#         elif  code == 500 or code == 503:
#             #if the server down:500, 503
#             #or some error system does not know: 000

#             #self.fake_browser.driver.save_screenshot('failed.png')
#             #raise CloseSpider('@@@@@@@@@@@@@@@@@@@@the server is down! Please try to run it later@@@@@@@@@@@@@@@@@')
#             print(f'Downloader: server is down! code{code}')
#             spider.close_it = f'server is down! code{code}'
#         else:
#             print(f'Downloader: unexpect error! code {code}')
#             spider.close_it = f'unexpect error! code{code}'

#         return response

#     def process_exception(self, request, exception, spider):
#         # Called when a download handler or a process_request()
#         # (from other downloader middleware) raises an exception.

#         # Must either:
#         # - return None: continue processing this exception
#         # - return a Response object: stops process_exception() chain
#         # - return a Request object: stops process_exception() chain
#         pass

#     def spider_opened(self, spider):
#         spider.logger.info('Spider opened: %s' % spider.name)
