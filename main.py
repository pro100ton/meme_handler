import json
import logging
import os
from meme_review.meme_review import REVIEW_CONVERSATION_HANDLER

from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHEEKE_BREEKE = os.getenv('CHANNEL_ID')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

updater = Updater(token=TOKEN)
dispatcher = updater.dispatcher

MEME, ANON = range(2)
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
                             text="Please, say 'yes' or 'no' (or /stop to stop suggestion)")
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
    dispatcher.add_handler(conversation_handler)
    dispatcher.add_handler(REVIEW_CONVERSATION_HANDLER)
    dispatcher.add_handler(MessageHandler((~Filters.command), help_handler))
    updater.start_polling()


if __name__ == '__main__':
    main()
