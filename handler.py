import re
from lxml import html
import requests

print("Reloading")

async def get_title(bot, target, source, url):
    resp = requests.get(url)
    if not resp:
        return None
    tree = html.fromstring(resp.content)
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

