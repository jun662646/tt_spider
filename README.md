# TikTok爬虫
## spider/tt.py
- 使用`selenium`模拟用户行为进行爬虫
## spider/tt1.py
- 使用`selenium-wire`模拟用户行为 + 监听浏览器请求进行爬虫
# 部署
## 打包成exe
```shell
pyinstaller .\start.spec
```
### 执行exe的必须文件
- scrapy.cfg
- tt.exe
- tt.xlsx
