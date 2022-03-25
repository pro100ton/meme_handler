import json
import os

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

START, REVIEW = range(2)
ADMIN_CHAT = os.getenv('ADMIN_CHAT_ID')


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
        posted_memes.append(current_meme)
        if current_meme["person_chat_id"] != ADMIN_CHAT:
            context.bot.send_message(chat_id=current_meme["person_chat_id"],
                                     text="Congratulations, one of your memes has been approved")
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
            json.dump(posted_memes, json_file, ensure_ascii=False)
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


def timeout(update, context):
    update.message.reply_text('You were AFK for too long, you may continue review again later')


def stop_bot(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Meme review stopped")
    return ConversationHandler.END


REVIEW_CONVERSATION_HANDLER = ConversationHandler(
    entry_points=[CommandHandler('start_review', review_start)],
    states={
        START: [
            MessageHandler(Filters.regex('^(Approve|Decline)$') & (~Filters.command), review_next),
        ],
        ConversationHandler.TIMEOUT: [MessageHandler(Filters.text | Filters.command, timeout)],
    },
    fallbacks=[CommandHandler('stop', stop_bot)],
    conversation_timeout=360
)
