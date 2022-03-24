import json
import logging
import os

from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

# def meme_review(update: Update, context: CallbackContext):
#     # Read data from memes queue
#     with open('queue.json') as json_file:
#         json_memes_queue = json.load(json_file)
#     with open('posts.json') as json_file:
#         json_memes_posts = json.load(json_file)
#     review_keyboard = [
#         ['Approve', 'Decline']
#     ]
#     review_markup = ReplyKeyboardMarkup(review_keyboard, one_time_keyboard=True)
#     for meme in json_memes_queue:
#         context.bot.send_photo(chat_id=update.effective_chat.id,
#                                photo=meme["meme"],
#                                caption=f"Sender: {meme['username']} : {meme['first_name']}\nAnonymous: {meme['anon']}",
#                                reply_markup=review_markup)

START, REVIEW = range(2)


def review_start(update: Update, context: CallbackContext) -> int:
    with open('queue.json') as json_file:
        json_memes_queue = json.load(json_file)
    if len(json_memes_queue) == 0:
        context.bot.send_message(chat_id=update.effective_chat.id, text="No memes left for review")
        return ConversationHandler.END
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Next meme:")
    with open('posts.json') as json_file:
        json_memes_posts = json.load(json_file)
    review_keyboard = [
        ['Approve', 'Decline']
    ]
    review_markup = ReplyKeyboardMarkup(review_keyboard, one_time_keyboard=True)
    meme = json_memes_queue[0]
    context.bot.send_photo(chat_id=update.effective_chat.id,
                           photo=meme["meme"],
                           caption=f"Sender: {meme['username']} : {meme['first_name']}\nAnonymous: {meme['anon']}",
                           reply_markup=review_markup)
    print(update.message.text)
    if update.message.text == 'Approve':
        # Remove from queue and add to posts file
        json_memes_queue.pop(0)
        json_memes_posts.append(meme)
        with open('../queue.json', 'w', encoding='utf-8') as json_file:
            json.dump(json_memes_queue, json_file, ensure_ascii=False)
        with open('../posts.json', 'w', encoding='utf-8') as json_file:
            json.dump(json_memes_posts, json_file, ensure_ascii=False)
    elif update.message.text == 'Decline':
        # Remove from queue file
        json_memes_queue.pop(0)
        with open('../queue.json', 'w', encoding='utf-8') as json_file:
            json.dump(json_memes_queue, json_file, ensure_ascii=False)
    return REVIEW


def timeout(update, context):
    update.message.reply_text('You were AFK for too long, to provide SUS memes please start over')


def stop_bot(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sad doge:(")
    return ConversationHandler.END


REVIEW_CONVERSATION_HANDLER = ConversationHandler(
    entry_points=[CommandHandler('start_review', review_start)],
    states={
        REVIEW: [
            MessageHandler(Filters.text, review_start),
        ],
        # ANON: [
        #     MessageHandler(Filters.regex('^(Yes|No)$'), name_confirm),
        #     MessageHandler((~Filters.regex('^(Yes|No)$') & ~Filters.command), wrong_answer),
        # ],
        ConversationHandler.TIMEOUT: [MessageHandler(Filters.text | Filters.command, timeout)],
    },
    fallbacks=[CommandHandler('stop', stop_bot)],
    conversation_timeout=360
)
