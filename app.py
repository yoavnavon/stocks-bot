
from utils import upload_to_aws

import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import logging
import os
import uuid

from telegram.ext import Updater, CommandHandler
from dotenv import load_dotenv
import yfinance as yf
import matplotlib
matplotlib.use('AGG')


# Load env variables
load_dotenv()

# Bot port
PORT = int(os.environ.get('PORT', '8443'))

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
TOKEN = os.environ['TOKEN']

sns.set_style("darkgrid")

PERIODS = set(['1d', '5d', '1mo', '3mo', '6mo',
              '1y', '2y', '5y', '10y', 'ytd', 'max'])
INTERVALS = set(['1m', '2m', '5m', '15m', '30m', '60m',
                '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo'])


def start(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hi there!')


def help(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def plot(update, context):

    args = context.args

    if not args:
        return update.message.reply_text('Please provide ticker as argument')

    ticker = args[0].upper()
    period = "1mo"
    interval = "1h"

    # Validate period arg
    if len(args) >= 2:
        period = args[1]
        if period not in PERIODS:
            return update.message.reply_text(f'{period} not a valid period')
        interval = "5m" if period.endswith('d') else interval

    # Validate interval arg
    if len(args) == 3:
        interval = args[2]
        if interval not in INTERVALS:
            return update.message.reply_text(f'{interval} not a valid interval')

    # Get historical market data
    stock = yf.Ticker(ticker)
    hist = stock.history(period=period, interval=interval)

    # If ticker is not valid, will appear in _ERRORS dict
    if ticker in yf.shared._ERRORS:
        return update.message.reply_text(f'{ticker} not a valid ticker')

    # Prepare data
    hist.index.rename('index', inplace=True)
    hist = hist.reset_index()
    hist['index_str'] = hist['index'].astype(str)
    hist['index_str'] = hist.index_str.apply(lambda label: label[5:-9])

    # Plot
    _, ax = plt.subplots(figsize=(12, 8))
    sns.lineplot(x='index_str', y='Close', data=hist, ax=ax)
    ax.set_xticks(np.linspace(0, len(hist)-1, num=5, dtype=int))
    ax.set_xlabel(ticker)
    ax.set_ylabel('value')
    ax.tick_params(axis='x', rotation=30)
    plt.savefig('image.png')
    plt.clf()

    # Upload chart to AWS so its available to anyone
    aws_file = f'{uuid.uuid4()}.png'
    aws_url = f'https://stocks-bot.s3-sa-east-1.amazonaws.com/{aws_file}'
    upload_to_aws('image.png', 'stocks-bot', aws_file)

    # Response
    update.message.reply_photo(aws_url)


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("plot", plot))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_webhook(listen="0.0.0.0",
                          port=int(PORT),
                          url_path=TOKEN,
                          webhook_url=f"{os.environ['WEBHOOK_URL']}/{TOKEN}"
                          )

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
