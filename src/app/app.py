"""
All of the API's endpoints
"""

import asyncio

from hypercorn.asyncio import serve
from hypercorn.config import Config
from quart import Quart
from twitchio.ext import commands

app = Quart(__name__)


@app.route('/webhook', methods=['POST'])
async def webhook():
    """
    Rest webhook event
    :return: message and status
    """
    print('Webhook was hit')
    return 'Success!', 200


async def run_hypercorn_app():
    """
    Start the app
    """
    config = Config()
    config.bind = ["0.0.0.0:50995"]
    config.workers = 1
    config.loglevel = "info"
    await serve(app, config)


async def run_app_and_bot(bot: commands.Bot):
    """
    Run twitch bot alongside hypercorn in the same async event loop
    :param bot: the bot that we are using
    """
    # Start the Hypercorn server
    hypercorn_task = asyncio.ensure_future(run_hypercorn_app())
    # Start the bot
    bot_task = asyncio.ensure_future(bot.connect())
    await bot_task
    await hypercorn_task
