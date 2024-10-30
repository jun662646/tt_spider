import logging
import time
from configparser import ConfigParser
from datetime import datetime, timedelta
from datetime import date

import pandas as pd
import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from tt_spider.items import TtItem
from tt_spider.spiders.Constants import X

logger = logging.getLogger('tt')

# 自定义配置
config = ConfigParser()
config.read('scrapy.cfg')
startDate = (datetime.strptime(config.get('tt', 'start'), '%Y-%m-%d')).date()
endDate = (datetime.strptime(config.get('tt', 'end'), '%Y-%m-%d')).date()

# webdriver配置
options = Options()
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument(f'--proxy-server=localhost:7890')

class TtSpider(scrapy.Spider):
    name = "tt"
    allowed_domains = ["tiktok.com"]

    # 读取Excel文件
    df = pd.read_excel('tt.xlsx', engine='openpyxl')
    urls = df.iloc[:, 2].tolist()
    start_urls = urls
    # start_urls = ['https://www.tiktok.com/@pipi.paw5']

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
                    yield from self.run(name)
                    break
        except Exception as e:
            errItem = TtItem()
            errItem['账号名'] = name
            errItem['备注'] = '爬虫异常'
            yield errItem
            logger.exception(e)
        finally:
            logger.warning(f'本页剩余{self.count}')

    def run(self, name):
        divs = self.driver.find_elements(By.XPATH, X.VIDEOS)
        self.count = len(divs)
        logger.warning('divs: %s', self.count)
        while self.count > 0:
            try:
                # 跳过直播
                live = self.driver.find_elements(By.XPATH, X.LIVE)
                # 卡在详情页
                close = self.driver.find_elements(By.XPATH, X.CLOSE_BUTTON)
                if len(close) > 0:
                    close[0].click()
                    logger.warning("跳出详情,%s", self.count)
                    continue
                if len(live) > 0:
                    self.driver.execute_script("arguments[0].remove();", live[0])
                    logger.warning("跳过直播,%s", self.count)
                    continue

                self.count -= 1
                button = WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, X.VIDEO)))
                plays = button.text.replace('已置顶', '').replace('刚刚看过','').strip()
                # 打开详情页
                button.click()
                # 日期
                dateTxt = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.XPATH, X.DATE))).text
                date = self.convertDate(dateTxt)
                logger.warning('d=%s,start=%s,end=%s',date,startDate,endDate)
                if date > endDate:
                    self.driver.execute_script("arguments[0].remove();", button)
                    continue
                elif date < startDate:
                    if len(self.driver.find_elements(By.XPATH, X.PIN)) == 0:
                        break
                    else:
                        self.driver.execute_script("arguments[0].remove();", button)
                        logger.warning("跳过置顶,%s", self.count)
                        continue

                # 点赞数
                likes = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, X.LIKES))).text

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
                button = self.driver.find_element(By.XPATH, X.CLOSE_BUTTON)
                button.click()

                divs = self.driver.find_elements(By.XPATH, X.VIDEOS)
                self.count = len(divs)
                # 下一个视频
                if self.count == 0:
                    logger.warning('下滑一屏幕')
                    # 屏幕滚动
                    self.driver.execute_script("window.scrollBy(0, 1000)")
                    time.sleep(2)
                    divs = self.driver.find_elements(By.XPATH, X.VIDEOS)
                    logger.warning('divs:%s', len(divs))
                    self.count = len(divs)
            except Exception as e:
                divs = self.driver.find_elements(By.XPATH, X.VIDEOS)
                self.count = len(divs)
                logger.exception('出现异常：%s,exception:%s', self.count, e)

    def convertDate(self, dateTxt):
        try:
            now = datetime.now()
            if '小时前' in dateTxt:
                d = int(dateTxt.replace('小时前','').strip())
                return (now - timedelta(hours=d)).date()
            elif '天前' in dateTxt:
                d = int(dateTxt.replace('天前','').strip())
                return (now - timedelta(days=d)).date()
            elif '周前' in dateTxt:
                d = int(dateTxt.replace('周前','').strip())
                return (now - timedelta(weeks=d)).date()
            elif '-' in dateTxt:
                d = dateTxt.split('-')
                if len(d) == 2:
                    return date(now.year, int(d[0]), int(d[1]))
                elif len(d) == 3:
                    return date(int(d[0]), int(d[1]), int(d[2]))
        except Exception as e:
            logger.exception("转换日期异常，date=%s, %s",dateTxt, e)
            return None

    def closed(self, reason):
        if self.driver:
            self.driver.quit()
            logger.warning("WebDriver closed")