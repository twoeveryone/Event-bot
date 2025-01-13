import discord
import aiohttp
import asyncio
import json
import os
from discord.ext import commands, tasks
from discord.ui import Button, View
from datetime import datetime

async def get_avatar_bytes(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.read()

# Замени 'YOUR_TOKEN' на токен твоего бота
TOKEN = 'YOUR_TOKEN'
YOUR_GUILD_ID = Сюда вставить
YOUR_EVENT_CHANNEL_ID = Сюда вставить  # Замените на ID вашего канала

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

participants_file = 'participants.json'
events_file = 'events.json'

def create_participants_database():
    if not os.path.exists(participants_file):
        with open(participants_file, 'w') as f:
            json.dump({}, f)

def create_events_database():
    if not os.path.exists(events_file):
        with open(events_file, 'w') as f:
            json.dump([], f)

def get_participants(event_name):
    if not os.path.exists(participants_file):
        create_participants_database()
    with open(participants_file, 'r') as f:
        participants = json.load(f)
    return participants.get(event_name, [])

def add_participant(event_name, user_id):
    if not os.path.exists(participants_file):
        create_participants_database()
    
    with open(participants_file, 'r') as f:
        participants = json.load(f)
    
    if event_name not in participants:
        participants[event_name] = []
    
    if user_id not in participants[event_name]:
        participants[event_name].append(user_id)
    
    with open(participants_file, 'w') as f:
        json.dump(participants, f)

def clear_participants(event_name):
    if not os.path.exists(participants_file):
        create_participants_database()
    
    with open(participants_file, 'r') as f:
        participants = json.load(f)
    
    if event_name in participants:
        del participants[event_name]
    
    with open(participants_file, 'w') as f:
        json.dump(participants, f)

def add_event(event):
    if not os.path.exists(events_file):
        create_events_database()
    
    with open(events_file, 'r') as f:
        events = json.load(f)
    
    events.append(event)
    
    with open(events_file, 'w') as f:
        json.dump(events, f, default=str)

def get_events():
    if not os.path.exists(events_file):
        create_events_database()
    
    with open(events_file, 'r') as f:
        events = json.load(f)
    
    return events

def update_event(updated_event):
    if not os.path.exists(events_file):
        create_events_database()
    
    with open(events_file, 'r') as f:
        events = json.load(f)
    
    for i, event in enumerate(events):
        if event['title'] == updated_event['title']:
            events[i] = updated_event
            break
    
    with open(events_file, 'w') as f:
        json.dump(events, f, default=str)

def delete_event(event_title):
    if not os.path.exists(events_file):
        create_events_database()
    
    with open(events_file, 'r') as f:
        events = json.load(f)
    
    events = [event for event in events if event['title'] != event_title]
    
    with open(events_file, 'w') as f:
        json.dump(events, f, default=str)

async def get_avatar_bytes(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.read()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    check_events.start()
    print(f'Logged in as {bot.user}')

@bot.command()
async def событие(ctx):
    guild = ctx.guild

    await ctx.send("Введите название события:")

    def check_name(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        title_msg = await bot.wait_for('message', check=check_name, timeout=60)
        title = title_msg.content

        await ctx.send("Введите описание события:")
        description_msg = await bot.wait_for('message', check=check_name, timeout=60)
        description = description_msg.content

        await ctx.send("Введите время начала события (например, 01-01-2024 12:00):")
        start_time_msg = await bot.wait_for('message', check=check_name, timeout=60)
        start_time = datetime.strptime(start_time_msg.content, "%d-%m-%Y %H:%M")

        await ctx.send("Упомяните ведущего для события (например, @User):")
        host_msg = await bot.wait_for('message', check=check_name, timeout=60)
        if not host_msg.mentions:
            await ctx.send("Вы не упомянули ведущего. Пожалуйста, попробуйте снова.")
            return
        selected_host = host_msg.mentions[0]

        await ctx.send(f'Вы выбрали ведущего: {selected_host.mention}')
        
        button = Button(label="Участвовать", style=discord.ButtonStyle.green)

        async def button_callback(interaction):

            add_participant(title, interaction.user.id)
            await interaction.response.send_message(f"{interaction.user.mention} вы участвуете в событии '{title}'!", ephemeral=True)

        button.callback = button_callback
        view = View()
        view.add_item(button)

        event_channel = guild.get_channel(YOUR_EVENT_CHANNEL_ID)
        message = f'**Событие:** {title}\n**Описание:** {description}\n**Время:** {start_time.strftime("%d-%m-%Y %H:%M")}\n**Ведущий:** {selected_host.mention}'
        await event_channel.send(message, view=view)

        event = {
            "title": title,
            "description": description,
            "start_time": start_time,
            "host_id": selected_host.id,
            "category_id": None
        }
        add_event(event)

        await ctx.send(f"Событие '{title}' создано и добавлено в расписание!")

    except asyncio.TimeoutError:
        await ctx.send("Время ожидания истекло. Пожалуйста, попробуйте снова.")

@tasks.loop(minutes=1)
async def check_events():
    now = datetime.now()
    events = get_events()

    for event in events:
        start_time = datetime.strptime(event["start_time"], "%Y-%m-%d %H:%M:%S")

        if start_time <= now and not event["category_id"]:
            guild = bot.get_guild(YOUR_GUILD_ID)
            host = guild.get_member(event["host_id"])

            category = await guild.create_category(f"{event['title']} - Category")
            voice_channel = await category.create_voice_channel(event['title'])

            event["category_id"] = category.id
            update_event(event)
            participants = get_participants(event["title"])
            for user_id in participants:
                user = await bot.fetch_user(user_id)
                if user:
                    await user.send(f"Событие '{event['title']}' началось! Подробности: {event['description']} Время: {start_time.strftime('%H:%M %d-%m-%Y')}")

            close_button = Button(label="Закрыть событие", style=discord.ButtonStyle.danger)

            async def close_button_callback(interaction):
                await voice_channel.delete()
                await category.delete()
                clear_participants(event["title"])
                delete_event(event["title"])
                await interaction.response.send_message("Событие завершено и все данные очищены.", ephemeral=True)

            close_button.callback = close_button_callback
            close_view = View()
            close_view.add_item(close_button)

            await host.send(f"Событие '{event['title']}' началось в {voice_channel.mention}.", view=close_view)

@bot.event
async def on_ready():
    try:
        print(f'Бот {bot.user} запущен!')
        await bot.change_presence(activity=discord.Game(name="Dev 2everyone"))
        await send_log(f'Бот {bot.user} запущен!')
    except Exception as e:
        print(f"Ошибка в on_ready: {e}")

bot.run(TOKEN)