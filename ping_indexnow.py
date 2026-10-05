# -*- coding: utf-8 -*-
"""把 site/sitemap.xml 里的全部 URL 推送给 IndexNow（Bing、Yandex 等共用）。

用法：git push 之后，等 Cloudflare 部署完成（线上能访问到密钥文件），再运行
    python build.py && python ping_indexnow.py
返回 200 / 202 表示已接收。
"""
import json, re, urllib.request
from urllib.parse import urlparse
# build.py 在 import 时就会执行整个构建，所以这里直接从源码里读这两个常量
_src = open("build.py", encoding="utf-8").read()
BASE_URL = re.search(r'^BASE_URL = "(.*?)"', _src, re.M).group(1)
INDEXNOW_KEY = re.search(r'^INDEXNOW_KEY = "(.*?)"', _src, re.M).group(1)

urls = re.findall(r"<loc>(.*?)</loc>", open("site/sitemap.xml", encoding="utf-8").read())
body = json.dumps({
    "host": urlparse(BASE_URL).netloc,
    "key": INDEXNOW_KEY,
    "keyLocation": "%s/%s.txt" % (BASE_URL, INDEXNOW_KEY),
    "urlList": urls,
}).encode("utf-8")
req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body,
                             headers={"Content-Type": "application/json; charset=utf-8"})
with urllib.request.urlopen(req) as r:
    print("IndexNow: HTTP %d, submitted %d URLs" % (r.status, len(urls)))
