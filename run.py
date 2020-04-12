import argparse
import logging

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from providers import Provider, Player

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# setup configuration
logger = logging.getLogger(__name__)
parser = argparse.ArgumentParser("Arguments for telegram authentication")
parser.add_argument("--token", help="Token authentication")
args = parser.parse_args()


_PLAYERS = []


def start(update, context):
    description = """
*CHESSTRAINER*
Welcome to 'chesstrainer' enjoy your chess and solve every puzzle.

*PGN(Portable Game Notation) english*
The answer must have below international format. 
e.g: _1. Rg5+ Bxg5 2. Qxg5#_

*Score assignment*
 (CA) - Correct Answer [+2]
 (U) - Unsolved [+/-0]
 (W)  - Wrong Answer [-1]
    """
    update.message.reply_text(description, parse_mode='Markdown')

def solution(update, context):
    chat_id = update.message.chat_id
    username = update.message.chat.username
    for p in _PLAYERS:
        if p.username == username:
            p.lock()
    solution = context._bot_data['provider'].get_solution()
    context.bot.send_message(chat_id=chat_id, text=f'*SOLUTION*: _{solution}_', parse_mode='Markdown')
    context.bot.send_message(chat_id=chat_id, text='You must wait until next puzzle will be released')

def play(update, context):
    chat_id = update.message.chat_id
    username = update.message.chat.username
    for p in _PLAYERS:
        if p.username == username:
            p.lock()
    provider = context._bot_data['provider']
    context.bot.send_message(chat_id=chat_id, text=f'You can play the position here: {provider.url}\n\n This won\'t to be considered for chess race ranking')


def puzzle(context):
    job = context.job
    if 'provider' in context._bot_data:
        del context._bot_data['provider']

    for p in _PLAYERS:
        p.unlock()

    p = Provider()
    context._bot_data.__setitem__('provider', p)
    context.bot.send_message(
        job.context, text=f'*TITLE*: _{p.title}_\n*MOVE*: {"WHITE" if p.white_to_move() else "BLACK"}', parse_mode='Markdown')
    context.bot.send_photo(chat_id=job.context, photo=p.image)

def verify_answer(update, context):
    provider = context._bot_data['provider']
    chat_id = update.message.chat_id
    username = update.message.chat.username
    _t = update.message.text.strip()
    _sol = provider.get_solution().strip()
    if _t == _sol:
        for p in _PLAYERS:
            if p.username == username:
                if not p.is_locked():
                    p._ca()
                    context.bot.send_message(chat_id=chat_id, text='Awesome!!\nCheck your /ranking position')
                else:
                    context.bot.send_message(chat_id=chat_id, text='Wait until next puzzle will be released')


    else:
        for p in _PLAYERS:
            if p.username == username:
                p._wa()
        context.bot.send_message(chat_id=chat_id, text='Nope!!\nYou lost 1 point')


def join(update, context):
    chat_id = update.message.chat_id
    username = update.message.chat.username
    if username not in [p.username for p in _PLAYERS]:
        _PLAYERS.append(Player(username=username))
        update.message.reply_text(f"New subscriber: *{username}*, welcome!!", parse_mode='Markdown')
    else:
        context.bot.send_message(chat_id=chat_id, text='!!Already registered to chess race')


def leave(update, context):
    chat_id = update.message.chat_id
    username = update.message.chat.username
    for i, p in enumerate(_PLAYERS):
        if p.username == username:
            _PLAYERS.pop(i)
            update.message.reply_text(f"Bye Bye: *{username}*!!", parse_mode='Markdown')
            return
    context.bot.send_message(chat_id=chat_id, text='!!Already left chess race, please /join with us.')


def ranking(update, context):
    chat_id = update.message.chat_id
    player_list = []
    for i, p in enumerate(sorted(_PLAYERS, key=lambda _p: _p.score, reverse=True)):
        _s = f"{i+1 if i < 3 else '..'} {p.username} "+"✅" if p.is_active() else "❌"
        _s = _s + f" {p.score}"
        player_list.append(_s)
    parse_player_list = '\n'.join(player_list)
    content = f"""
*PLAYERS/SCORE*

{parse_player_list}
    
"""
    context.bot.send_message(chat_id=chat_id, text=content, parse_mode='Markdown')

def players(update, context):
    chat_id = update.message.chat_id
    if len(_PLAYERS) == 0:
        context.bot.send_message(chat_id=chat_id, text='No players registered to the chess race')
    else:
        context.bot.send_message(chat_id=chat_id, text='TODO LIST PLAYER')



def admin_start(update, context):
    """Add a job to the queue."""
    chat_id = update.message.chat_id
    interval = int(context.args[0])
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

    update.message.reply_text('The chess race has stopped! See you later..')

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
    dp.add_handler(CommandHandler("help", start))
    dp.add_handler(CommandHandler("join", join))
    dp.add_handler(CommandHandler("leave", leave))
    dp.add_handler(CommandHandler("solution", solution))
    dp.add_handler(CommandHandler("play", play))
    dp.add_handler(MessageHandler(Filters.regex(r"(1\.)(.*)"), verify_answer))
    dp.add_handler(CommandHandler("ranking", ranking))
    dp.add_handler(CommandHandler("players", players))
    dp.add_handler(CommandHandler("admin_start", admin_start,
                                  pass_args=True,
                                  pass_job_queue=True,
                                  pass_chat_data=True))
    dp.add_handler(CommandHandler("admin_stop", stop, pass_chat_data=True))

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
