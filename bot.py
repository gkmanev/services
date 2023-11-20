#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.

import asyncio
import time
import schedule
from threading import Thread
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, KeyboardButton, ReplyKeyboardMarkup, constants
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,    
)
from utils import WindCheck, check_services
import aioschedule




# Stages
START_ROUTES, END_ROUTES = range(2)
# Callback data
#ONE, TWO, THREE, FOUR, FIVE = range(5)
STATUS = 6
SERVICES = 7
WIND = 1
ARIS = 2
POWER = 3
ELASTICITY = 4
HPP = 5
ENTSOE = 8
START_OVER = 9

initial_keyboard = [
    [
        InlineKeyboardButton("Status Wind", callback_data=str(STATUS)),                  
    ]
]

msg_list = []

def my_periodic_function():
    # Your logic here
    check_list = msg_list.copy()  # Create a copy of msg_list to compare
    msgs = check_services(is_called_from_menu=False)
    
    msg_list.clear()  # Clear the original msg_list before appending new messages
    msg_list.extend(msgs)  # Extend the list with new messages
    # Check for differences between dictionaries
    differences = []

    for check_dict in msg_list:
        if check_dict not in check_list:
            differences.append(check_dict)

    if differences:
        print("Differences found:")
        for diff in differences:
            print(diff)
    else:
        print("No differences found.")
   
   
    print(f"check_list: {check_list} ||| msg_list: {msg_list}")

def schedule_thread():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Schedule the function to run every 1 hour
schedule.every(30).seconds.do(my_periodic_function)

# Start the scheduling thread
thread = Thread(target=schedule_thread)
thread.start()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send message on `/start`."""
    # Get user that sent /start and log his name

    reply_markup = InlineKeyboardMarkup(initial_keyboard)
    # Send message with text and appended InlineKeyboard
    await update.message.reply_text("Entra Energy Services", reply_markup=reply_markup)
    # Tell ConversationHandler that we're in state `FIRST` now
    return START_ROUTES


async def start_over(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Prompt same text & keyboard as `start` does but not as new message"""
    # Get CallbackQuery from Update
    query = update.callback_query
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()

    reply_markup = InlineKeyboardMarkup(initial_keyboard)
    # Instead of sending a new message, edit the message that
    # originated the CallbackQuery. This gives the feeling of an
    # interactive menu.
    await query.edit_message_text(text="Welcome to Entra Energy services status!", reply_markup=reply_markup)
    return START_ROUTES


async def wind_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
        
    await query.answer()    
    
    # Send a preloader message (like "Loading...")
    await query.edit_message_text(
        text="Loading....⏳",
        parse_mode=constants.ParseMode.HTML
    )
    services = check_services(is_called_from_menu=True)
    print(services)
    formatted_text = '\n'.join(services)    
    
    await query.edit_message_text(
        text= f'<b>{formatted_text}</b>',        
        parse_mode= constants.ParseMode.HTML
    )
    return START_ROUTES


  
application = Application.builder().token("6615001834:AAEwtOD_EVyFYrOPHk_GdHgkdEKxRHFUc-4").build()

# Setup conversation handler with the states FIRST and SECOND
# Use the pattern parameter to pass CallbackQueries with specific
# data pattern to the corresponding handlers.
# ^ means "start of line/string"
# $ means "end of line/string"
# So ^ABC$ will only allow 'ABC'
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        START_ROUTES: [
            #CallbackQueryHandler(all_services, pattern="^" + str(SERVICES) + "$"),
            CallbackQueryHandler(wind_status, pattern="^" + str(STATUS) + "$"),
        ],
        END_ROUTES: [
            #CallbackQueryHandler(start_over, pattern="^" + str(ONE) + "$"),
            #CallbackQueryHandler(end, pattern="^" + str(TWO) + "$"),
        ],
    },
    fallbacks=[CommandHandler("start", start)],
)

# Add ConversationHandler to application that will be used for handling updates
application.add_handler(conv_handler)

# Run the bot until the user presses Ctrl-C
application.run_polling(allowed_updates=Update.ALL_TYPES)


