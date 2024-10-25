# from scrapy import cmdline
from tt_spider.spiders import tt
# cmdline.execute('scrapy crawl tt'.split())

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

process = CrawlerProcess(get_project_settings())
process.crawl('tt')
process.start()