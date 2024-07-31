import asyncio
import json
import random

from aiogram import Bot, Dispatcher, types
import aiocron

import credentials

TOKEN = credentials.bot_token
DATA_FILE = "data.json"
MEMBER_FILE = "reminders.json"

# All handlers should be attached to the Router (or Dispatcher)
dp = Dispatcher()
bot = Bot(TOKEN)


async def add_bounty_statement(statement_category:str, statement_content:str, data_file_path:str) -> bool:
    '''
    Add statement to provided data file in the requested category

    returns succes representation as bool
    '''
    with open(data_file_path, 'r', encoding='utf-8') as read_data_file:
        file_dict = json.load(read_data_file)
    file_dict[statement_category] = file_dict[statement_category] + [statement_content]
    with open(data_file_path, 'w', encoding='utf-8') as write_data_file:
        if file_dict:
            write_data_file.write(json.dumps(file_dict))

    return True


async def update_subscriber_list(user_id:str, add:bool, member_file_path:str) -> bool:
    '''
    add or remove requested user from subscription list by user_id. ensure no duplicates occur
    '''
    with open(member_file_path, 'r', encoding='utf-8') as read_data_file:
        file_dict = json.load(read_data_file)
    if add:
        if user_id not in file_dict['members']:
            file_dict['members'] = file_dict['members'] + [user_id]
    else:
        if user_id in file_dict['members']:
            file_dict['members'] = file_dict['members'].remove(user_id)
    with open(member_file_path, 'w', encoding='utf-8') as write_data_file:
        if file_dict['members']:
            write_data_file.write(json.dumps(file_dict))
        else:
            write_data_file.write(json.dumps({'members': []}))

    return True


async def clean_bot_mention(content, bot_username) -> str:
    '''
    clean mention of @USERNAME from command to avoid accidently adding it to input data
    '''
    return content.replace("@" + bot_username, "")


async def verify_admins(id) -> bool:
    if id in (542003050, 6679289069, 274999563, 281788046):
        return True


@dp.message()
async def message_handler(message: types.Message) -> None:
    """
    """
    if message.text.startswith('/start'):
        await bot.send_message(message.chat.id, 'welkom bij de reminder bot')
    elif message.text.startswith('/help'):
        help_message = "bounty Bot help:\n"
        help_message += "\n/sub - adds you to the list of reminders"
        help_message += "\n/unsub removes you from the list of reminders"
        # help_message += "\n/add_greeting GREETINGTEXT"
        # help_message += "\n/add_body BODYTEXT"
        # help_message += "\n/add_ending ENDINGTEXT"
        await bot.send_message(message.chat.id, help_message)

    # handle additions of greeting, body or ending
    elif message.text.startswith('/add_greeting '):
        if await verify_admins(message.from_user.id):
            content = message.text.replace("/add_greeting ", "")
            content = await clean_bot_mention(content=content, bot_username=credentials.bot_username)
            if await add_bounty_statement(statement_category='greeting', statement_content=content, data_file_path=DATA_FILE):
                await bot.send_message(message.chat.id, f'added:\n"{content}"\nAs: greeting')
            else:
                await bot.send_message(message.chat.id, 'ERROR IDK WERKTE NIET')

    elif message.text.startswith('/add_body '):
        if await verify_admins(message.from_user.id):
            content = message.text.replace("/add_body ", "")
            content = await clean_bot_mention(content=content, bot_username=credentials.bot_username)
            if await add_bounty_statement(statement_category='body', statement_content=content, data_file_path=DATA_FILE):
                await bot.send_message(message.chat.id, f'added:\n"{content}"\nAs: body')
            else:
                await bot.send_message(message.chat.id, 'ERROR IDK WERKTE NIET')

    elif message.text.startswith('/add_ending '):
        if await verify_admins(message.from_user.id):
            content = message.text.replace("/add_ending ", "")
            content = await clean_bot_mention(content=content, bot_username=credentials.bot_username)
            if await add_bounty_statement(statement_category='ending', statement_content=content, data_file_path=DATA_FILE):
                await bot.send_message(message.chat.id, f'added:\n"{content}"\nAs: ending')
            else:
                await bot.send_message(message.chat.id, 'ERROR IDK WERKTE NIET')

    # handle signing up and signing out of bounty reminders
    elif message.text.startswith('/sub'):
        await update_subscriber_list(user_id=message.from_user.id, member_file_path=MEMBER_FILE, add=True)
        await bot.send_message(message.chat.id, 'ADDED to the list')
    elif message.text.startswith('/unsub'):
        await update_subscriber_list(user_id=message.from_user.id, member_file_path=MEMBER_FILE, add=False)
        await bot.send_message(message.chat.id, 'REMOVED from the list')


async def main() -> None:

    @aiocron.crontab('0 5,16,19 * * * 0')
    async def sendReminders():
        '''
        '''
        print("sending reminders x1")
        with open(MEMBER_FILE, 'r', encoding='utf-8') as member_data_file:
            member_dict = json.load(member_data_file)

            with open(DATA_FILE, 'r', encoding='utf-8') as quote_data_file:
                data_dict = json.load(quote_data_file)
                msg_greeting, msg_body, msg_ending = random.choice(data_dict['greeting']), random.choice(data_dict['body']), random.choice(data_dict['ending'])
                for member in member_dict['members']:
                    try:
                        await bot.send_message(member, f"{msg_greeting}\n\n{msg_body}\n\n{msg_ending}")
                    except Exception as e:
                        pass # some fool probably blocked the bot, I cba to deal with that

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())