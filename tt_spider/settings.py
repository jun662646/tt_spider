from datetime import datetime

BOT_NAME = "tt_spider"

SPIDER_MODULES = ["tt_spider.spiders"]
NEWSPIDER_MODULE = "tt_spider.spiders"

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
   "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
   "Accept-Language": "en",
}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
   "tt_spider.middlewares.TtSpiderDownloaderMiddleware": 543,
   # "tt_spider.middlewares.SeleniumMiddleware": 545,
}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
   "tt_spider.pipelines.TtSpiderPipeline": 300,
}


# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

FEED_EXPORTERS = {
   'csv': 'scrapy.exporters.CsvItemExporter',
}

FEEDS = {
   'tt.csv': {
      'format': 'csv',
      'overwrite': True,
      'encoding': 'utf-8',
      'fields': ['账号名','播放','点赞','url','日期','备注'],
   },
}

# 日志
LOG_LEVEL = 'WARNING'
LOG_ENABLED = True
LOG_STDOUT = True
LOG_ENCODING='utf-8'
to_day = datetime.now()
# LOG_FILE = 'logs/tt_{}_{}_{}.log'.format(to_day.year, to_day.month, to_day.day)
LOG_FILE_APPEND = True

ROBOTSTXT_OBEY = False
DOWNLOAD_DELAY = 3