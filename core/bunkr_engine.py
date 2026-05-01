import os
import base64
import aiohttp
import re
from math import floor
from itertools import cycle
from urllib.parse import urlparse
from core.progress import ProgressUpdater

BUNKRR_DOMAINS = ("bunkr.si", "bunkr.fi", "bunkr.ru", "bunkr.cr", "bunkr.rip", "bunkrr.su")
BUNKRR_DOWNLOAD_HEADERS = {"User-Agent": "Mozilla/5.0", "Referer": "https://get.bunkrr.su/"}

def is_bunkr_url(url):
    return any(dom in url for dom in BUNKRR_DOMAINS)

def decrypt(api_resp):
    try:
        t = api_resp["timestamp"]
        enc = base64.b64decode(api_resp["url"])
        key = f"SECRET_KEY_{floor(t/3600)}".encode("utf-8")
        dec = bytearray(b ^ next(cycle(key)) for b in enc)
        return dec.decode("utf-8", errors="ignore")
    except: return None

async def download_bunkr(url: str, updater: ProgressUpdater):
    updater.action_text = "Fetching Bunkr API"
    updater.update_sync(10, "API", "Wait")

    slug_match = re.search(r"/([a-zA-Z0-9_-]+)$", url)
    if not slug_match: raise Exception("Invalid Bunkr URL")
    slug = slug_match.group(1)

    api_resp = None
    async with aiohttp.ClientSession() as session:
        for dom in BUNKRR_DOMAINS:
            try:
                async with session.post(f"https://{dom}/api/vs", json={"slug": slug}, headers=BUNKRR_DOWNLOAD_HEADERS, timeout=10) as resp:
                    if resp.status == 200:
                        api_resp = await resp.json()
                        break
            except: continue

    if not api_resp: raise Exception("Could not fetch Bunkr API. Site might be down.")

    dl_link = decrypt(api_resp)
    if not dl_link: raise Exception("Bunkr decryption failed.")

    updater.action_text = "Downloading Bunkr File"
    tmp_dir = "tmp_downloads"
    os.makedirs(tmp_dir, exist_ok=True)
    filename = os.path.join(tmp_dir, urlparse(dl_link).path.rstrip("/").split("/")[-1])

    async with aiohttp.ClientSession() as session:
        async with session.get(dl_link, headers=BUNKRR_DOWNLOAD_HEADERS) as resp:
            total_size = int(resp.headers.get('content-length', 0))
            downloaded = 0
            with open(filename, 'wb') as f:
                async for chunk in resp.content.iter_chunked(65536):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        updater.update_sync(percent, "Bunkr", "Calc...")

    return filename