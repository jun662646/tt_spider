import json
from datetime import datetime, timedelta, date

import scrapy
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from seleniumwire import webdriver
from seleniumwire.utils import decode

from tt_spider.items import TtItem

options = {
    'proxy': {
        'http': 'http://127.0.0.1:7890',
        'https': 'https://127.0.0.1:7890',
        'no_proxy': 'localhost,127.0.0.1'
    },
}
chrome_options = Options()
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
driver = webdriver.Chrome(options=chrome_options, seleniumwire_options=options)

class TtSpider(scrapy.Spider):
    name = "tt1"
    allowed_domains = ["tiktok.com"]
    start_urls = [
        # 'https://www.tiktok.com/@myrabbani13',
        # 'https://www.tiktok.com/@rasidah.rasidah73'
        'http://www.tiktok.com/@dianna.0583',
        'https://www.tiktok.com/@iram12itam',
        'http://www.tiktok.com/@dianna.0583',
        'http://www.tiktok.com/@dianna.0583',
    ]

    def __init__(self):
        # self.driver = webdriver.Chrome(seleniumwire_options=options, service=Service('chromedriver.exe'))
        self.driver = driver

    def parse(self, response):
        self.driver.get(response.url)
        try:
            WebDriverWait(self.driver, 30).until(EC.any_of(
                # 正常账号
                EC.element_to_be_clickable((By.XPATH, '//*[@id="main-content-others_homepage"]/div/div[2]/div[2]/div/div[1]')),
                # 私密账号
                EC.visibility_of_element_located((By.XPATH, '//*[@id="main-content-others_homepage"]/div/div/div/p[1]')),
                # 找不到账号
                EC.visibility_of_element_located((By.XPATH, '//*[@id="main-content-others_homepage"]/div/main/div/p[1]')),
            ))
            name = response.url.split('@')[1]
            print('name:'+name)

            c1 = self.driver.find_elements(By.XPATH, '//*[@id="main-content-others_homepage"]/div/div/div/p[1]')
            c2 = self.driver.find_elements(By.XPATH, '//*[@id="main-content-others_homepage"]/div/main/div/p[1]')
            if len(c1) > 0:
                errItem = TtItem()
                errItem['账号名'] = name
                errItem['备注'] = '私密账号'
                yield errItem
            elif len(c2) > 0:
                errItem = TtItem()
                errItem['账号名'] = name
                errItem['备注'] = '找不到账号'
                yield errItem
            else:
                divs = self.driver.find_elements(By.XPATH, '//*[@id="main-content-others_homepage"]/div/div[2]/div[2]/div/div')
                print('divs:', len(divs))

                # 遍历所有请求并打印信息
                for request in self.driver.requests:
                    if 'item_list/' in request.url:
                        try:
                            body = decode(request.response.body, request.response.headers.get('Content-Encoding', 'identity')).decode('utf-8')
                            if body.strip():
                                try:
                                    json_response = json.loads(body)
                                    if 'itemList' in json_response and 'cursor' in json_response:
                                        for item in json_response['itemList']:
                                            ttItem = TtItem()
                                            ttItem['id'] = item['id']
                                            ttItem['发布时间'] = datetime.fromtimestamp(item['createTime'])
                                            ttItem['账号名'] = item['author']['uniqueId']
                                            ttItem['昵称'] = item['author']['nickname']
                                            ttItem['url'] = 'https://www.tiktok.com/@'+item['author']['uniqueId']+'/video/'+item['id']
                                            ttItem['播放'] = item['stats']['playCount']
                                            ttItem['点赞'] = item['stats']['diggCount']
                                            ttItem['评论'] = item['stats']['commentCount']
                                            ttItem['收藏'] = item['stats']['collectCount']
                                            ttItem['分享'] = item['stats']['shareCount']
                                            if ttItem['发布时间'].date() > date.today() - timedelta(days=7):
                                                yield ttItem
                                            else:
                                                if not item.get('isPinnedItem', False): break
                                except json.JSONDecodeError as e:
                                    print("Response is not JSON:", e)
                        except Exception as e:
                            print("Error decoding response:", e)
        finally:
            pass
            # self.driver.quit()  # 关闭浏览器

    def closed(self, reason):
        if self.driver:
            # self.driver.quit()
            print("WebDriver closed")