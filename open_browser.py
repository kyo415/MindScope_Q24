"""Đợi API sẵn sàng rồi mới mở trình duyệt (được chạy bởi file .bat)."""
from __future__ import annotations

import json
import time
import urllib.request
import webbrowser

URL = 'http://127.0.0.1:5055'
for _ in range(60):
    try:
        with urllib.request.urlopen(f'{URL}/api/health', timeout=1) as response:
            if json.load(response).get('status') == 'ok':
                webbrowser.open(URL)
                break
    except (OSError, ValueError):
        pass
    time.sleep(0.5)
