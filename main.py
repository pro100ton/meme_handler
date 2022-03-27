import json
import logging
import os
import datetime
import pytz
from time import timezone

from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from queue_manager.meme_queue import manage_meme_queue
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler, Job

load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHEEKE_BREEKE = os.getenv('CHANNEL_ID')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

updater = Updater(token=TOKEN)
job_queue = updater.job_queue
dispatcher = updater.dispatcher
TIMEZONE = pytz.timezone('Europe/Moscow')

MEME, ANON, START, REVIEW = range(4)
ADMIN_CHAT = os.getenv('ADMIN_CHAT_ID')
anon_keyboard = [
    ['Yes', 'No']
]
markup = ReplyKeyboardMarkup(anon_keyboard, one_time_keyboard=True)


def help_handler(update: Update, context: CallbackContext):
    start_keyboard = [
        ['/start']
    ]
    start_markup = ReplyKeyboardMarkup(start_keyboard, one_time_keyboard=True)
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="To start suggesting memes, send /start command",
                             reply_markup=start_markup)


def post_meme_on_schedule(context: CallbackContext):
    logging.warning("TASK TRIGGERED")
    message = context.job.context[0]
    if message["anon"]:
        tmp_caption = f"#Предложка от анонимуса"
    else:
        tmp_caption = f"#Предложка от @{message['username']}"
    context.bot.send_photo(chat_id=CHEEKE_BREEKE,
                           photo=message["meme"],
                           caption=tmp_caption)


def start_conversation(update: Update, context: CallbackContext) -> int:
    context.user_data["meme_id"] = None
    context.bot.send_message(chat_id=update.effective_chat.id, text="Please, upload much SUS meme")
    return MEME


def wrong_data(update: Update, context: CallbackContext) -> int:
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Please, provide SUS picture, not some other bullshit (or /stop to stop suggestion)")
    return MEME


def wrong_answer(update: Update, context: CallbackContext) -> int:
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Please, say 'yes' or 'no' (or /stop to stop suggestion)\n"
                                  "Also you allowed to provide only one meme per suggestion, "
                                  "so if you sent more than one - than only first one will be sent to review")
    return ANON


def stop_bot(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sad doge:(")
    return ConversationHandler.END


def name_confirm(update: Update, context: CallbackContext):
    suggestion_result = {
        "person_chat_id": update.message.from_user["id"],
        "first_name": update.message.from_user["first_name"],
        "username": update.message.from_user["username"],
        "meme": context.user_data.get("meme_id", "No meme id"),
        "anon": (True if update.message.text == "Yes" else False)
    }
    with open('queue.json') as json_file:
        json_data = json.load(json_file)
        json_data.append(suggestion_result)
    with open('queue.json', 'w', encoding='utf-8') as json_file:
        json.dump(json_data, json_file, ensure_ascii=False)
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f"Thanks for your much SUS meme. It will be reviewed soon (or not)")
    return ConversationHandler.END


def handle_uploaded_meme(update: Update, context: CallbackContext) -> int:
    file_id = update.message.photo[0]["file_id"]
    context.user_data["meme_id"] = file_id
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Do you want to be sneaky anonymous?",
                             reply_markup=markup)
    return ANON


def done_suggestion(update: Update, context: CallbackContext) -> int:
    context.bot.send_photo(chat_id=CHEEKE_BREEKE, text="Conversation ended")
    return ConversationHandler.END


def timeout(update, context):
    update.message.reply_text('You were AFK for too long, to provide SUS memes please start over')


# MEME REVIEW HANDLERS
def review_start(update: Update, context: CallbackContext) -> int:
    with open('queue.json') as json_file:
        context.bot_data["queued_memes"] = json.load(json_file)
    if len(context.bot_data["queued_memes"]) == 0 or context.bot_data["queued_memes"] == "[]":
        context.bot.send_message(chat_id=update.effective_chat.id, text="No memes left for review")
        return ConversationHandler.END
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Next meme:")
    with open('posts.json') as json_file:
        context.bot_data["post_memes"] = json.load(json_file)
    review_keyboard = [
        ['Approve', 'Decline']
    ]
    review_markup = ReplyKeyboardMarkup(review_keyboard, one_time_keyboard=True)
    context.bot_data["current_meme"] = context.bot_data.get("queued_memes")[0]
    current_meme = context.bot_data.get("current_meme")
    context.bot.send_photo(chat_id=update.effective_chat.id,
                           photo=current_meme["meme"],
                           caption=f"Sender: {current_meme['username']} : {current_meme['first_name']}\nAnonymous: {current_meme['anon']}",
                           reply_markup=review_markup)
    return START


def review_next(update: Update, context: CallbackContext) -> int:
    # Getting necessary data
    queued_memes = context.bot_data.get("queued_memes")
    posted_memes = context.bot_data.get("post_memes")
    current_meme = context.bot_data.get("current_meme")
    if update.message.text == 'Approve':
        # Remove from queue and add to posts file
        queued_memes.pop(0)
        posted_memes = manage_meme_queue(posted_memes, current_meme)
        # Add new queued task
        post_time = datetime.datetime.strptime(posted_memes[-1]["post_time"], "%Y-%m-%d %H:%M:%S")
        post_time = TIMEZONE.localize(post_time)
        job_queue.run_once(post_meme_on_schedule, post_time, context=(current_meme,))
        if current_meme["person_chat_id"] != ADMIN_CHAT:
            context.bot.send_message(chat_id=current_meme["person_chat_id"],
                                     text=f"Congratulations, one of your memes has been approved and will be posted at {post_time}")
    elif update.message.text == 'Decline':
        # Remove from queue file
        queued_memes.pop(0)
        if current_meme["person_chat_id"] != ADMIN_CHAT:
            context.bot.send_message(chat_id=current_meme["person_chat_id"],
                                     text="Unforch, but one of your memes has been declined:(")
    if len(queued_memes) == 0:
        context.bot.send_message(chat_id=update.effective_chat.id, text="That was the last meme")
        with open('queue.json', 'w') as json_file:
            json_file.write('[]')
        with open('posts.json', 'w', encoding='utf-8') as json_file:
            json.dump(posted_memes, json_file, ensure_ascii=False, default=str)
        return ConversationHandler.END
    current_meme = queued_memes[0]
    # Set new values for the review data
    context.bot_data["queued_memes"] = queued_memes
    context.bot_data["post_memes"] = posted_memes
    context.bot_data["current_meme"] = current_meme
    review_keyboard = [
        ['Approve', 'Decline']
    ]
    review_markup = ReplyKeyboardMarkup(review_keyboard, one_time_keyboard=True)
    context.bot.send_photo(chat_id=update.effective_chat.id,
                           photo=current_meme["meme"],
                           caption=f"Sender: {current_meme['username']} : {current_meme['first_name']}\nAnonymous: {current_meme['anon']}",
                           reply_markup=review_markup)
    return START


def review_timeout(update, context):
    update.message.reply_text('You were AFK for too long, you may continue review again later')


def review_stop_bot(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Meme review stopped")
    return ConversationHandler.END


def main() -> None:
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_conversation)],
        states={
            MEME: [
                MessageHandler(Filters.photo, handle_uploaded_meme),
                MessageHandler((~Filters.photo & ~Filters.command), wrong_data),
            ],
            ANON: [
                MessageHandler(Filters.regex('^(Yes|No)$'), name_confirm),
                MessageHandler((~Filters.regex('^(Yes|No)$') & ~Filters.command), wrong_answer),
            ],
            ConversationHandler.TIMEOUT: [MessageHandler(Filters.text | Filters.command, timeout)],
        },
        fallbacks=[CommandHandler('stop', stop_bot)],
        conversation_timeout=360
    )
    meme_review_conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start_review', review_start)],
        states={
            START: [MessageHandler(Filters.regex('^(Approve|Decline)$') & (~Filters.command), review_next)],
            ConversationHandler.TIMEOUT: [MessageHandler(Filters.text | Filters.command, review_timeout)],
        },
        fallbacks=[CommandHandler('stop', review_stop_bot)],
        conversation_timeout=360
    )
    dispatcher.add_handler(conversation_handler)
    dispatcher.add_handler(meme_review_conversation_handler)
    dispatcher.add_handler(MessageHandler((~Filters.command), help_handler))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
