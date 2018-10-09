import re

print("Reloading")

async def get_title(bot, target, source, message):
    return "..."

def find_urls(message):
    matches = re.findall(r'\bhttps?://[^ \t]+\b', message)

    tidied_matches = []
    for match in matches:
        if match.endswith(')') or match.endswith(','):
            match = match[:-1]
        tidied_matches.append(match)

    return tidied_matches

