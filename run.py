import argparse
import datetime
import logging

from telegram.ext import Updater, CommandHandler
from providers import Provider

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# setup configuration
logger = logging.getLogger(__name__)
parser = argparse.ArgumentParser("Arguments for telegram authentication")
parser.add_argument("--token", help="Token authentication")
args = parser.parse_args()



def start(update, context):
    update.message.reply_text('Welcome to "chesstrainer" enjoy your chess and solve every puzzle.')

def solution(update, context):
    chat_id = update.message.chat_id
    solution = context._bot_data['provider'].get_solution()
    context.bot.send_message(chat_id=chat_id, text=f'*SOLUTION*: _{solution}_', parse_mode='Markdown')


def puzzle(context):
    job = context.job
    if 'provider' in context._bot_data:
        del context._bot_data['provider']

    p = Provider()
    context._bot_data.__setitem__('provider', p)
    context.bot.send_message(
        job.context, text=f'*TITLE*: _{p.title}_\n*MOVE*: {"WHITE" if p.white_to_move() else "BLACK"}', parse_mode='Markdown')
    context.bot.send_photo(chat_id=job.context, photo=p.image)

def join(update, context):
    """Add a job to the queue."""
    chat_id = update.message.chat_id
    interval = 5
    try:
        # Add job to queue and stop current one if there is a timer already
        job = context.job_queue.run_repeating(puzzle, interval, context=chat_id)
        context.chat_data['job'] = job
        update.message.reply_text('New puzzle is coming soon..')

    except (IndexError, ValueError):
        update.message.reply_text('Something goes wrong')

def stop(update, context):
    job = context.chat_data['job']
    job.schedule_removal()
    del context.chat_data['job']

    update.message.reply_text('Bye! As soon as possible..')

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    """Run bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(args.token, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("join", join))
    dp.add_handler(CommandHandler("solution", solution))
    dp.add_handler(CommandHandler("set", join,
                                  pass_args=True,
                                  pass_job_queue=True,
                                  pass_chat_data=True))
    dp.add_handler(CommandHandler("stop", stop, pass_chat_data=True))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
    # SIGABRT. This should be used most of the time, since start_polling() is
    # non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()
