import aiohttp
import re
from lxml import html

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

    return title

def find_urls(message):
    matches = re.findall(r'\bhttps?://[^ \t]+\b', message)

    tidied_matches = []
    for match in matches:
        if match.endswith(')') or match.endswith(','):
            match = match[:-1]
        tidied_matches.append(match)

    return tidied_matches

