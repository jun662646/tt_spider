import logging
import time
from datetime import datetime

import pandas as pd
import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from tt_spider.items import TtItem

logger = logging.getLogger('tt')

X_VIDEOS = '//*[@data-e2e="user-post-item-list"]/div'
X_VIDEO  = '//*[@data-e2e="user-post-item-list"]/div[1]'
X_CLOSE_BUTTON = '//*[@data-e2e="browse-close"]'
X_DATE = '//*[@data-e2e="browser-nickname"]/span[3]'
X_LIKES = '//*[@data-e2e="browse-like-count"]'
# X_ACCOUNT_ERROR   = '//*[@class="css-1y4x9xk-PTitle emuynwa1"]'
X_ACCOUNT_ERROR   = '//*[contains(@class, "emuynwa1")]'
X_LIVE = '//*[@class="css-x6y88p-DivItemContainerV2 e19c29qe17"]'
X_PIN = '//*[@data-e2e="video-card-badge"]'

X_VERIFY_CODE = '//*[starts-with(@id, ":")]/div/div[1]/div/button'
X_REFRESH_BUTTON = '//*[@id="main-content-others_homepage"]/div/div[2]/main/div/button|//*[@id="main-content-others_homepage"]/div/main/div/button'
X_LOGIN = '//*[@id="loginContainer"]/div/div/div[3]/div/div[2]'

options = Options()
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument(f'--proxy-server=localhost:7890')

class TtSpider(scrapy.Spider):
    name = "tt"
    allowed_domains = ["tiktok.com"]

    # 读取Excel文件
    df = pd.read_excel('tt.xlsx', engine='openpyxl')
    urls = df['主页链接'].tolist()
    start_urls = urls
    # start_urls = ['https://www.tiktok.com/@chisooraa']

    def __init__(self):
        self.driver = webdriver.Chrome(options=options)
        self.count = 0
        self.nameCount = 0

    def parse(self, response):
        name = response.url.split('@')[1]
        self.nameCount+=1
        logger.warning(f'第{self.nameCount}个，name:{name}')
        try:
            self.driver.get(response.url)
            while True:
                WebDriverWait(self.driver, 30).until(EC.any_of(
                    # 正常账号
                    EC.element_to_be_clickable((By.XPATH, X_VIDEO)),
                    # 异常账号
                    EC.visibility_of_element_located((By.XPATH, X_ACCOUNT_ERROR)),
                    # 验证码
                    EC.visibility_of_element_located((By.XPATH, X_VERIFY_CODE)),
                    # 刷新
                    EC.visibility_of_element_located((By.XPATH, X_REFRESH_BUTTON)),
                    # 游客登录
                    EC.visibility_of_element_located((By.XPATH, X_LOGIN)),
                ))
                err1 = self.driver.find_elements(By.XPATH, X_VERIFY_CODE)
                err2 = self.driver.find_elements(By.XPATH, X_REFRESH_BUTTON)
                err3 = self.driver.find_elements(By.XPATH, X_LOGIN)
                err4 = self.driver.find_elements(By.XPATH, X_ACCOUNT_ERROR)
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
                else:
                    yield from self.run(name)
                    break
        except Exception as e:
            errItem = TtItem()
            errItem['账号名'] = name
            errItem['备注'] = '爬虫异常'
            yield errItem
            logger.warning(e)
        finally:
            logger.warning(f'本页剩余{self.count}')

    def run(self, name):
        divs = self.driver.find_elements(By.XPATH, X_VIDEOS)
        self.count = len(divs)
        logger.warning('divs: %s', self.count)
        while self.count > 0:
            try:
                # 跳过直播
                live = self.driver.find_elements(By.XPATH, X_LIVE)
                # 卡在详情页
                close = self.driver.find_elements(By.XPATH, X_CLOSE_BUTTON)
                if len(close) > 0:
                    close[0].click()
                    logger.warning("跳出详情,%s", self.count)
                    continue
                if len(live) > 0:
                    self.driver.execute_script("arguments[0].remove();", live[0])
                    logger.warning("跳过直播,%s", self.count)
                    continue

                self.count -= 1
                button = WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, X_VIDEO)))
                plays = button.text.replace('已置顶', '').replace('刚刚看过','').strip()
                # 打开详情页
                button.click()
                # 日期
                date = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.XPATH, X_DATE))).text
                if '-' in date:
                    if len(self.driver.find_elements(By.XPATH, X_PIN)) == 0:
                        logger.warning("跳过置顶,%s", self.count)
                        break
                    else:
                        self.driver.execute_script("arguments[0].remove();", button)
                        continue

                # 点赞数
                likes = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, X_LIKES))).text

                item = TtItem()
                item['账号名'] = name
                item['url'] = self.driver.current_url
                item['播放'] = plays
                item['点赞'] = likes
                item['日期'] = date

                yield item

                # 使用 JavaScript 来删除元素
                self.driver.execute_script("arguments[0].remove();", button)

                # 关闭详情页
                button = self.driver.find_element(By.XPATH, X_CLOSE_BUTTON)
                button.click()

                divs = self.driver.find_elements(By.XPATH, X_VIDEOS)
                self.count = len(divs)
                # 下一个视频
                if self.count == 0:
                    logger.warning('下滑一屏幕')
                    # 屏幕滚动
                    self.driver.execute_script("window.scrollBy(0, 1000)")
                    time.sleep(2)
                    divs = self.driver.find_elements(By.XPATH, X_VIDEOS)
                    logger.warning('divs:%s', len(divs))
                    self.count = len(divs)
            except Exception as e:
                logger.warning('出现异常：%s,exception:%s', self.count, e)
                pass

    def closed(self, reason):
        if self.driver:
            self.driver.quit()
            logger.warning("WebDriver closed")