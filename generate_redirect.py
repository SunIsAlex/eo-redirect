#!/usr/bin/env python3
"""
获取 EO Pages 预览 token，生成 redirect.html
由 GitHub Actions 每1小时调用一次
"""

import http.client
import json
import ssl
import os
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

    return {
        "token":     data["Data"]["Response"]["Token"],
        "timestamp": str(data["Data"]["Response"]["Timestamp"]),
    }


def generate_html(token: str, timestamp: str) -> str:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
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
    <p><a id="link" href="#">点击这里手动跳转</a></p>
    <p style="font-size:12px;color:#aaa">Token 更新于 {now}</p>
  </div>
  <script>
    const eoDomain  = "https://{EO_DOMAIN}";
    const eoToken   = "{token}";
    const eoTime    = "{timestamp}";

    // 透传用户访问的路径和查询参数
    const path      = window.location.pathname;
    const search    = window.location.search;
    const separator = search ? "&" : "?";
    const target    = eoDomain + path + search + separator
                      + "eo_token=" + eoToken + "&eo_time=" + eoTime;

    document.getElementById("link").href = target;
    window.location.replace(target);
  </script>
</body>
</html>"""


if __name__ == "__main__":
    print(f"正在获取 token: {EO_DOMAIN}")
    data = fetch_token()
    print(f"Token: {data['token']}, Timestamp: {data['timestamp']}")

    html = generate_html(data["token"], data["timestamp"])
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"已写入 {OUTPUT_FILE}")
