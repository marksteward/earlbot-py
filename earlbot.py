import asyncio
from datetime import datetime
from importlib import reload
import os
from pytz import utc, timezone
import sqlite3
import sys
import yaml

import aionotify
from pydle import Client

from handler import handler


def adapt_ts(dt):
    return int(dt.timestamp())

def convert_ts(i):
    dt = datetime.fromtimestamp(float(i), utc)
    return dt.astimezone(timezone('Europe/London'))

sqlite3.register_adapter(datetime, adapt_ts)
sqlite3.register_converter('timestamp', convert_ts)


class EarlBot(Client):
    def __init__(self, config):
        self.config = config
        self.db = sqlite3.connect(config['db'], detect_types=sqlite3.PARSE_COLNAMES)
        self.current_nick = None

        kwargs = {
           'realname': 'Earlbot',
        }
        if 'sasl_password' in self.config:
            kwargs.update({
                'sasl_username': self.config.get('sasl_username', self.config['nick']),
                'sasl_password': self.config['sasl_password'],
            })

        super().__init__(config['nick'], **kwargs)

    async def connect(self, *args, **kwargs):
        kwargs.update({
            'tls': True,
            'tls_verify': True,
            'password': self.config['password'],
        })
        await super().connect(self.config['host'], *args, **kwargs)

    async def on_connect(self):
        print("Connected, joining channels")
        for channel in self.config['channels']:
            if not channel:
                print("Missing channel, make sure to use quotes around channel names")
                continue
            await asyncio.sleep(0.8)
            # FIXME: wait for the channel to sync before continuing
            print(f"Joining {channel}")
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
        print(f"Nick for {old} now {new}")
        self.current_nick = new
        if old == self.current_nick:
            print("Updated own nick")

        elif old == '<unregistered>' and new != self.current_nick:
            print(f"Nick is {new}, attempting to regain earlbot")
            await self.message('nickserv', 'regain')

    async def on_message(self, target, source, message):
        print(target, source, message)
        if source == self.current_nick:
            return

        if not hasattr(handler, 'process_message'):
            print("Error: no process_message handler")
            return

        if self.is_channel(target):
            channel = target
            respond_to = channel
        else:
            # Mostly match perl for now, although it seems to also have $$* for announcements?
            channel = 'msg'
            respond_to = source

        await handler.process_message(self, message, source, respond_to, channel)


async def watch_handler():
    flags = aionotify.Flags.MODIFY | aionotify.Flags.CREATE | aionotify.Flags.MOVED_TO | aionotify.Flags.IGNORED
    dir_ = os.path.dirname(handler.__file__)
    file_ = os.path.basename(handler.__file__)
    watcher = aionotify.Watcher()
    watcher.watch(dir_, flags)
    loop = asyncio.get_event_loop()
    await watcher.setup(loop)

    while True:
        event = await watcher.get_event()

        if event.name == '' and event.flags & aionotify.Flags.IGNORED:
            print("inotify watch was removed by OS, cannot reload automatically")
            break

        if event.name != file_:
            continue

        try:
            reload(handler)
        except Exception as e:
            print(f"Exception reloading: {e}")

    watcher.close()


async def main():
    config = yaml.safe_load(open(sys.argv[1], 'r'))
    bot = config['bots'][0]

    client = EarlBot(bot)
    await asyncio.gather(
        client.connect(),
        watch_handler(),
    )


asyncio.run(main())

