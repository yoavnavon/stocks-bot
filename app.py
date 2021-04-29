
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import os
from dotenv import load_dotenv
import yfinance as yf
import matplotlib
matplotlib.use('AGG') 
import matplotlib.pyplot as plt
import boto3
from botocore.exceptions import NoCredentialsError
import uuid

load_dotenv()
PORT = int(os.environ.get('PORT', '8443'))

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
TOKEN = os.environ['TOKEN']

# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hi there!')

def help(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')

def upload_to_aws(local_file, bucket, s3_file):
    s3 = boto3.client('s3', aws_access_key_id=os.environ['ACCESS_KEY'],
                      aws_secret_access_key=os.environ['SECRET_KEY'])

    try:
        s3.upload_file(local_file, bucket, s3_file)
        print("Upload Successful")
        return True
    except FileNotFoundError:
        print("The file was not found")
        return False
    except NoCredentialsError:
        print("Credentials not available")
        return False




def data(update, context):
  
    msft = yf.Ticker("MSFT")

    # get historical market data
    hist = msft.history(period="30d")

    hist['Close'].plot(figsize=(16, 9))
    plt.savefig('image.png')
    aws_file = f'{uuid.uuid4()}.png'
    aws_url = f'https://stocks-bot.s3-sa-east-1.amazonaws.com/{aws_file}'
    
    upload_to_aws('image.png', 'stocks-bot', aws_file)
    update.message.reply_photo(aws_url)

def echo(update, context):
    """Echo the user message."""
    update.message.reply_text(update.message.text)

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
    dp.add_handler(CommandHandler("chart", data))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, echo))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_webhook(listen="0.0.0.0",
                          port=int(PORT),
                          url_path=TOKEN,
                          webhook_url=os.environ['WEBHOOK_URL'] + TOKEN
                          )

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()