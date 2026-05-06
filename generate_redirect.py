#!/usr/bin/env python3
"""
获取 EO Pages 预览 token，生成 redirect.html
由 GitHub Actions 每2小时调用一次
"""

import http.client
import json
import ssl
import os
import urllib.parse
from datetime import datetime

EO_API_TOKEN = os.environ["EO_API_TOKEN"]
EO_DOMAIN    = os.environ.get("EO_DOMAIN", "cn-sunisalex-pages.zh-cn.edgeone.cool")
OUTPUT_FILE  = os.environ.get("OUTPUT_FILE", "index.html")

def fetch_token():
    payload = json.dumps({
        "Action": "DescribePagesEncipherToken",
        "Text": EO_DOMAIN,
    }).encode()

    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection("pages-api.edgeone.ai", timeout=15, context=ctx)
    conn.request("POST", "/v1", body=payload, headers={
        "Authorization": f"Bearer {EO_API_TOKEN}",
        "Content-Type": "application/json",
        "Content-Length": str(len(payload)),
    })
    resp = conn.getresponse()
    data = json.loads(resp.read().decode())
    conn.close()

    if data.get("Code") != 0:
        raise RuntimeError(f"API 错误: {data}")

    token     = data["Data"]["Response"]["Token"]
    timestamp = data["Data"]["Response"]["Timestamp"]
    return f"https://{EO_DOMAIN}?eo_token={token}&eo_time={timestamp}"


def generate_html(url: str) -> str:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="refresh" content="0;url={url}">
  <title>跳转中...</title>
  <style>
    body {{ font-family: sans-serif; display: flex; align-items: center;
            justify-content: center; height: 100vh; margin: 0; background: #f5f5f5; }}
    .box {{ text-align: center; color: #555; }}
    a {{ color: #0066cc; }}
  </style>
</head>
<body>
  <div class="box">
    <p>正在跳转，请稍候...</p>
    <p><a href="{url}">点击这里手动跳转</a></p>
    <p style="font-size:12px;color:#aaa">Token 更新于 {now}</p>
  </div>
</body>
</html>"""


if __name__ == "__main__":
    print(f"正在获取 token: {EO_DOMAIN}")
    url = fetch_token()
    print(f"预览 URL: {url}")

    html = generate_html(url)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"已写入 {OUTPUT_FILE}")
