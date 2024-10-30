import json
import logging
from configparser import ConfigParser
from datetime import datetime

import pandas as pd
import scrapy
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from seleniumwire import webdriver
from seleniumwire.utils import decode

from tt_spider.items import TtItem
from tt_spider.spiders.Constants import X

logger = logging.getLogger('tt')

# 自定义配置
config = ConfigParser()
config.read('scrapy.cfg')
startDate = (datetime.strptime(config.get('tt', 'start'), '%Y-%m-%d')).date()
endDate = (datetime.strptime(config.get('tt', 'end'), '%Y-%m-%d')).date()

seleniumwire_options = {
    'proxy': {
        'http': 'http://127.0.0.1:7890',
        'https': 'https://127.0.0.1:7890',
        'no_proxy': 'localhost,127.0.0.1'
    },
}
options = Options()
options.add_argument('--disable-blink-features=AutomationControlled')
# driver = webdriver.Chrome(options=options, seleniumwire_options=seleniumwire_options)

class TtSpider(scrapy.Spider):
    name = "tt1"
    allowed_domains = ["tiktok.com"]

    # 读取Excel文件
    df = pd.read_excel('tt.xlsx', engine='openpyxl')
    urls = df.iloc[:, 2].tolist()
    start_urls = urls
    # start_urls = ['https://www.tiktok.com/@venommovie']

    def __init__(self):
        self.driver = webdriver.Chrome(options=options, seleniumwire_options=seleniumwire_options)
        self.nameCount = 0
        self.start_time = datetime.now()

    def parse(self, response):
        name = response.url.split('@')[1]
        self.nameCount+=1
        logger.warning(f'第{self.nameCount}个，name:{name}')
        try:
            self.driver.get(response.url)
            while True:
                WebDriverWait(self.driver, 60).until(EC.any_of(
                    # 正常账号
                    EC.element_to_be_clickable((By.XPATH, X.VIDEO)),
                    # 异常账号
                    EC.visibility_of_element_located((By.XPATH, X.ACCOUNT_ERROR)),
                    # 验证码
                    EC.visibility_of_element_located((By.XPATH, X.VERIFY_CODE)),
                    # 刷新
                    EC.visibility_of_element_located((By.XPATH, X.REFRESH_BUTTON)),
                    # 游客登录
                    EC.visibility_of_element_located((By.XPATH, X.LOGIN)),
                ))
                err1 = self.driver.find_elements(By.XPATH, X.VERIFY_CODE)
                err2 = self.driver.find_elements(By.XPATH, X.REFRESH_BUTTON)
                err3 = self.driver.find_elements(By.XPATH, X.LOGIN)
                err4 = self.driver.find_elements(By.XPATH, X.ACCOUNT_ERROR)
                err5 = self.driver.find_elements(By.XPATH, X.VIDEO)
                if len(err1) > 0:
                    err1[0].click()
                    logger.warning("跳过验证码")
                elif len(err2) > 0:
                    err2[0].click()
                    logger.warning("点击刷新")
                elif len(err3) > 0:
                    logger.warning("点击游客登录")
                    err3[0].click()
                elif len(err4) > 0:
                    logger.warning("异常账号")
                    errItem = TtItem()
                    errItem['账号名'] = name
                    errItem['备注'] = err4[0].text
                    yield errItem
                    break
                elif len(err5) > 0:
                    yield from self.run()
                    break
        except Exception as e:
            errItem = TtItem()
            errItem['账号名'] = name
            errItem['备注'] = '爬虫异常'
            yield errItem
            logger.exception(e)

    def run(self):
        count = 0
        try:
            closed = {}
            flag = True
            while flag:
                json_response = {}
                # 找到当前页数据的请求
                for request in reversed(self.driver.requests):
                    if '/post/item_list/' in request.url and request.response is not None:
                        try:
                            body = decode(request.response.body, request.response.headers.get('Content-Encoding', 'identity')).decode('utf-8')
                            if body.strip():
                                try:
                                    json_response = json.loads(body)
                                    cursor = json_response.get('cursor')
                                    if 'itemList' in json_response and cursor is not None and cursor not in closed:
                                        closed[cursor] = 1
                                        break
                                except json.JSONDecodeError as e: logger.exception(e)
                        except Exception as e: logger.exception(e)
                # 没有数据，结束了
                if not json_response: break

                logger.warning("size=%s", len(json_response['itemList']))
                nextPage = True
                for item in json_response['itemList']:
                    date = datetime.fromtimestamp(item['createTime']).date()
                    isPinned = item.get('isPinnedItem', False)
                    logger.warning("now=%s,start=%s,end=%s,pin=%s", date,startDate,endDate,isPinned)
                    if date < startDate and not isPinned:
                        nextPage = False
                        break
                    if date > endDate or date < startDate and isPinned:
                        if isPinned : logger.warning("跳过置顶")
                    else:
                        ttItem = TtItem()
                        ttItem['账号名'] = item['author']['uniqueId']
                        ttItem['url'] = 'https://www.tiktok.com/@'+item['author']['uniqueId']+'/video/'+item['id']
                        ttItem['播放'] = item['stats']['playCount']
                        ttItem['点赞'] = item['stats']['diggCount']
                        ttItem['日期'] = date
                        # ttItem['id'] = item['id']
                        # ttItem['昵称'] = item['author']['nickname']
                        # ttItem['评论'] = item['stats']['commentCount']
                        # ttItem['收藏'] = item['stats']['collectCount']
                        # ttItem['分享'] = item['stats']['shareCount']
                        count += 1
                        yield ttItem
                #翻页
                hasMore = json_response.get('hasMore', False)
                if nextPage and hasMore:
                    videos = self.driver.find_elements(By.XPATH, X.VIDEOS)
                    # 屏幕滚动
                    logger.warning('下滑一屏幕, last=%s, cursor=%s', len(videos), json_response.get('cursor'))
                    self.driver.execute_script("window.scrollBy(0, 1000)")
                    WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, f'{X.VIDEOS}[{len(videos) + 1}]')))
                else:
                    flag = False
        finally:
            logger.warning('收集数量：%s', count)

    def closed(self, reason):
        if self.driver:
            self.driver.quit()
            print("WebDriver closed")
            logger.error('总耗时：%s', datetime.now()-self.start_time)
