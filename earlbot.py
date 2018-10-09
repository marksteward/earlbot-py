import asyncio
from datetime import datetime
from importlib import reload
import os
import sqlite3
import sys
import yaml

import aionotify
from pydle import MinimalClient

import handler

def adapt_ts(dt):
    return int(dt.timestamp())

def convert_ts(i):
    return datetime.utcfromtimestamp(float(i))

sqlite3.register_adapter(datetime, adapt_ts)
sqlite3.register_converter('timestamp', convert_ts)


class EarlBot(MinimalClient):
    def __init__(self, config):
        self.config = config
        self.db = sqlite3.connect(config['db'], detect_types=sqlite3.PARSE_COLNAMES)
        self.current_nick = None

        super().__init__(config['nick'], realname='Earlbot')

    async def connect(self):
        await super().connect(self.config['host'], tls=True, tls_verify=True, password=self.config['password'])

    async def on_connect(self):
        for channel in self.config['channels']:
            await self.join(channel)

    def get_url(self, url, channel):
        c = self.db.cursor()
        c.execute('select nick, timestamp as "ts [timestamp]" from uri where uri = ? and channel = ?', [url, channel])
        r = c.fetchone()
        c.close()
        return r

    def save_url(self, url, source, timestamp, channel):
        c = self.db.cursor()
        c.execute('insert into uri (uri, nick, timestamp, channel) values (?, ?, ?, ?)',
                  [url, source, timestamp, channel])
        self.db.commit()

    async def on_nick_change(self, old, new):
        print("Nick now {}".format(new))
        self.current_nick = new

    async def on_message(self, target, source, message):
        if source == self.current_nick:
            return

        if not hasattr(handler, 'find_urls'):
            return

        if self.is_channel(target):
            channel = target
        else:
            # Mostly match perl for now, although it seems to also have $$* for announcements?
            channel = 'msg'

        now = datetime.utcnow()

        urls = handler.find_urls(message)
        for url in urls:
            olde = self.get_url(url, channel)
            if not olde:
                self.save_url(url, source, now, channel)

            if hasattr(handler, 'get_title'):
                title = await handler.get_title(self, target, source, url)
                if title:
                        msg = '[ {} ]'.format(title)
                        if olde:
                            nick, timestamp = olde
                            msg += ' (First posted by {}, {})'.format(nick, timestamp.strftime('%c'))
                        await self.message(target, msg)


config = yaml.safe_load(open(sys.argv[1], 'r'))

bot = config['bots'][0]

loop = asyncio.get_event_loop()
client = EarlBot(bot)
asyncio.ensure_future(client.connect(), loop=loop)

async def watch_handler():
    flags = aionotify.Flags.MODIFY | aionotify.Flags.CREATE | aionotify.Flags.MOVED_TO | aionotify.Flags.IGNORED
    dir_ = os.path.dirname(handler.__file__)
    file_ = os.path.basename(handler.__file__)
    watcher = aionotify.Watcher()
    watcher.watch(dir_, flags)
    await watcher.setup(loop)

    while True:
        event = await watcher.get_event()

        if event.name == '' and flags & aionotify.Flags.IGNORED:
            print("inotify watch was removed by OS, cannot reload automatically")
            break

        if event.name != file_:
            continue

        try:
            reload(handler)
        except Exception as e:
            print("Exception reloading: {}".format(e))

    watcher.close()

asyncio.ensure_future(watch_handler(), loop=loop)

loop.run_forever()

