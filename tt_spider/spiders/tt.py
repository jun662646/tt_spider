import logging
import time

import pandas as pd
import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from tt_spider.items import TtItem

# 配置日志记录
logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s %(levelname)s:%(message)s',
                    filename='tt.log',
                    filemode='a')

X_VIDEOS = '//*[@data-e2e="user-post-item-list"]/div'
X_VIDEO  = '//*[@data-e2e="user-post-item-list"]/div[1]'
X_CLOSE_BUTTON = '//*[@data-e2e="browse-close"]'
X_DATE = '//*[@data-e2e="browser-nickname"]/span[3]'
X_LIKES = '//*[@data-e2e="browse-like-count"]'
X_ACCOUNT_ERROR   = '//*[@class="css-1y4x9xk-PTitle emuynwa1"]'
X_LIVE = '//*[@class="css-rpbd6e-SpanLiveBadge e139luw93"]'
X_PIN = '//*[@data-e2e="video-card-badge"]'

X_VERIFY_CODE = '//*[starts-with(@id, ":")]/div/div[1]/div/button'
X_REFRESH_BUTTON = '//*[@id="main-content-others_homepage"]/div/div[2]/main/div/button|//*[@id="main-content-others_homepage"]/div/main/div/button'
X_LOGIN = '//*[@id="loginContainer"]/div/div/div[3]'

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

    def __init__(self):
        self.driver = webdriver.Chrome(options=options)
        self.count = 0
        self.nameCount = 0

    def parse(self, response):
        self.driver.get(response.url)
        name = response.url.split('@')[1]
        logging.info(f'{name} ....... start .......')
        try:
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
                if len(err1) > 0:
                    err1[0].click()
                elif len(err2) > 0:
                    err2[0].click()
                elif len(err3) > 0:
                    err3[0].click()
                else:
                    break

            self.nameCount+=1
            print(f'第{self.nameCount}个，name:{name}')

            yield from self.run(name)
        except Exception as e:
            errItem = TtItem()
            errItem['账号名'] = name
            errItem['备注'] = '爬虫异常'
            yield errItem
        finally:
            print(self.count)

    def run(self, name):
        err = self.driver.find_elements(By.XPATH, X_ACCOUNT_ERROR)
        if len(err) > 0:
            errItem = TtItem()
            errItem['账号名'] = name
            errItem['备注'] = err[0].text
            yield errItem
        else:
            divs = self.driver.find_elements(By.XPATH, X_VIDEOS)
            print('divs:', len(divs))
            self.count = len(divs)
            while self.count > 0:
                try:
                    # 卡在详情页
                    live = self.driver.find_elements(By.XPATH, X_LIVE)
                    close = self.driver.find_elements(By.XPATH, X_CLOSE_BUTTON)
                    if len(close) > 0:
                        close[0].click()
                        continue
                    if len(live) > 0:
                        self.driver.execute_script("arguments[0].remove();", live[0])
                        continue

                    button = WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, X_VIDEO)))
                    self.count -= 1

                    try:
                        plays = button.text.replace('已置顶', '').replace('刚刚看过','').strip()
                    except Exception as e:
                        # TikTok有概率出现首个视频自动播放看不到播放数量，直接跳过
                        # self.driver.execute_script("arguments[0].remove();", button)
                        plays = ''
                    # 打开详情页
                    button.click()
                    # 日期
                    date = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.XPATH, X_DATE))).text
                    if '-' in date and len(self.driver.find_elements(By.XPATH, X_PIN)) == 0:
                        break

                    # 点赞数
                    likes = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, X_LIKES))).text

                    # print('plays:', plays)
                    # print('likes:' + likes)
                    # print('date:', date)

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
                        print('下滑一屏幕')
                        # 屏幕滚动
                        self.driver.execute_script("window.scrollBy(0, 1000)")
                        time.sleep(2)
                        divs = self.driver.find_elements(By.XPATH, X_VIDEOS)
                        print('divs:', len(divs))
                        self.count = len(divs)
                except Exception as e:
                    pass

    def closed(self, reason):
        if self.driver:
            self.driver.quit()
            print("WebDriver closed")