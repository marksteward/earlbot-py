import aiohttp
import re
from lxml import html

from urlextract import URLExtract

print("Reloading")

async def get_title(bot, target, source, url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            resp = await resp.text()

    if not resp:
        return None

    tree = html.fromstring(resp)
    title = tree.find(".//title").text
    if not title:
        return "dunno"

    return title.replace('\n', ' ')

def find_urls(message):
    extractor = URLExtract()
    matches = extractor.find_urls(message)

    tidied_matches = []
    for match in matches:
        if match.endswith(')') or match.endswith(','):
            match = match[:-1]

        if not match.startswith('http'):
            match = 'http://' + match

        tidied_matches.append(match)

    return tidied_matches

