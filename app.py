
from utils import plot_history, upload_to_aws

import seaborn as sns
import logging
import os
import uuid
from functools import wraps

from telegram.ext import Updater, CommandHandler
from telegram import ChatAction
from dotenv import load_dotenv
import yfinance as yf
import matplotlib
import matplotlib.pyplot as plt

matplotlib.use('AGG')
sns.set_style("darkgrid")


# Load env variables
load_dotenv()

# Bot port
PORT = int(os.environ.get('PORT', '8443'))

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
TOKEN = os.environ['TOKEN']


PERIODS = set(['1d', '5d', '1mo', '3mo', '6mo',
              '1y', '2y', '5y', '10y', 'ytd', 'max'])
INTERVALS = set(['1m', '2m', '5m', '15m', '30m', '60m',
                '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo'])


def send_typing_action(func):
    """Sends typing action while processing func command."""

    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(
            chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        return func(update, context,  *args, **kwargs)

    return command_func


@send_typing_action
def start(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hi there!')


def help(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


@send_typing_action
def plot(update, context):

    args = context.args

    if not args:
        return update.message.reply_text('Please provide ticker as argument')

    ticker = args[0].upper()
    interval = "1h"
    period = "1y"

    # Validate interval arg
    if len(args) == 2:
        interval = args[1]
        if interval not in INTERVALS:
            return update.message.reply_text(f'{interval} not a valid interval')
        if interval.endswith('m'):
            period = "1mo"

    # Get historical market data
    stock = yf.Ticker(ticker)
    hist = stock.history(period=period, interval=interval, prepost=True)

    # If ticker is not valid, will appear in _ERRORS dict
    if ticker in yf.shared._ERRORS:
        return update.message.reply_text(f'{yf.shared._ERRORS[ticker]}')

    # Keep last data points
    hist = hist.tail(100)

    # Plot
    plot_history(hist, ticker)
    plt.savefig('image.png', bbox_inches='tight')
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
