import os
import asyncio
import discord
from src.log import logger

from g4f.client import Client
from g4f.Provider import (RetryProvider, FreeGpt, ChatgptNext, AItianhuSpace,
                        You, OpenaiChat, FreeChatgpt, Liaobots,
                        Gemini, Bing)

from src.aclient import discordClient
from discord import app_commands
from src import log, art, personas


def run_discord_bot():
    @discordClient.event
    async def on_ready():
        await discordClient.send_start_prompt()
        await discordClient.tree.sync()
        loop = asyncio.get_event_loop()
        loop.create_task(discordClient.process_messages())
        logger.info(f'{discordClient.user} is now running!')


    @discordClient.tree.command(name="ask", description="Задайте вопрос ChatGPT")
    async def chat(interaction: discord.Interaction, *, message: str):
        if discordClient.is_replying_all == "True":
            await interaction.response.defer(ephemeral=False)
            await interaction.followup.send(
                "> **ПРЕДУПРЕЖДАЮ: вы уже перешли в режим отправки ответов. Если вы хотите использовать команду через /, переключитесь в обычный режим, снова используйте `/replyall`**")
            logger.warning("\x1b[31mВы уже перешли в режим ответа, не можете использовать: slash command!\x1b[0m")
            return
        if interaction.user == discordClient.user:
            return
        username = str(interaction.user)
        discordClient.current_channel = interaction.channel
        logger.info(
            f"\x1b[31m{username}\x1b[0m : /chat [{message}] in ({discordClient.current_channel})")

        await discordClient.enqueue_message(interaction, message)


    @discordClient.tree.command(name="private", description="Переключение на личное")
    async def private(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        if not discordClient.isPrivate:
            discordClient.isPrivate = not discordClient.isPrivate
            logger.warning("\x1b[31mSwitch to private mode\x1b[0m")
            await interaction.followup.send(
                "> **ИНФОРМАЦИЯ: Далее ответ будет отправлен через личные сообщение. Если вы хотите вернуться в открытый режим, используйте `/public`**")
        else:
            logger.info("Вы уже перешли в приватный режим!")
            await interaction.followup.send(
                "> **ПРЕДУПРЕЖДАЮ: у вас уже включен приватный режим. Если вы хотите переключиться в публичный режим, используйте `/public`**")


    @discordClient.tree.command(name="public", description="Переключение на публичное")
    async def public(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        if discordClient.isPrivate:
            discordClient.isPrivate = not discordClient.isPrivate
            await interaction.followup.send(
                "> **ИНФОРМАЦИЯ: Далее ответ будет отправлен непосредственно на канал. Если вы хотите вернуться в приватный режим, используйте `/private`**")
            logger.warning("\x1b[31mSwitch to public mode\x1b[0m")
        else:
            await interaction.followup.send(
                "> **ПРЕДУПРЕЖДАЮ: вы уже используете общедоступный режим. Если вы хотите переключиться в приватный режим, используйте `/private`**")
            logger.info("You already on public mode!")


    @discordClient.tree.command(name="replyall", description="Переключить доступ ко всем ответам")
    async def replyall(interaction: discord.Interaction):
        discordClient.replying_all_discord_channel_id = str(interaction.channel_id)
        await interaction.response.defer(ephemeral=False)
        if discordClient.is_replying_all == "True":
            discordClient.is_replying_all = "False"
            await interaction.followup.send(
                "> **ИНФОРМАЦИЯ: Далее бот ответит на команду с `/`. Если вы хотите вернуться в режим ответа на все вопросы, используйте `/replyAll`**")
            logger.warning("\x1b[31mSwitch to normal mode\x1b[0m")
        elif discordClient.is_replying_all == "False":
            discordClient.is_replying_all = "True"
            await interaction.followup.send(
                "> **ИНФОРМАЦИЯ: Далее бот отключит команды и будет отвечать только на все сообщения в этом канале. Если вы хотите вернуться в обычный режим, используйте `/replyAll`**")
            logger.warning("\x1b[31mSwitch to replyAll mode\x1b[0m")


    @discordClient.tree.command(name="chat-model", description="Переключите модель чата между «Gemini» и «GPT-4»")
    @app_commands.choices(model=[
        app_commands.Choice(name="gemini", value="gemini"),
        app_commands.Choice(name="gpt-4", value="gpt-4"),
        app_commands.Choice(name="gpt-3.5-turbo", value="gpt-3.5-turbo"),
    ])
    async def chat_model(interaction: discord.Interaction, model: app_commands.Choice[str]):
        await interaction.response.defer(ephemeral=True)
        try:
            if model.value == "gemini":
                discordClient.reset_conversation_history()
                discordClient.chatBot = Client(provider=RetryProvider([Gemini, FreeChatgpt], shuffle=False))
                discordClient.chatModel = model.value
            elif model.value == "gpt-4":
                discordClient.reset_conversation_history()
                discordClient.chatBot = Client(provider=RetryProvider([Liaobots, You, OpenaiChat, Bing], shuffle=False))
                discordClient.chatModel = model.value
            elif model.value == "gpt-3.5-turbo":
                discordClient.reset_conversation_history()
                discordClient.chatBot = Client(provider=RetryProvider([FreeGpt, ChatgptNext, AItianhuSpace], shuffle=False))
                discordClient.chatModel = model.value

            await interaction.followup.send(f"> **ИНФОРМАЦИЯ: Модель чата переключена на {model.name}.**")
            logger.info(f"Switched chat model to {model.name}")

        except Exception as e:
            await interaction.followup.send(f'> **Модель переключения с ошибкой: {e}**')
            logger.error(f"Ошибка переключения модели чата: {e}")

    @discordClient.tree.command(name="reset", description="Полный сброс истории разговоров")
    async def reset(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        discordClient.conversation_history = []
        await interaction.followup.send("> **ИНФОРМАЦИЯ: Я все забыл.**")
        personas.current_persona = "standard"
        logger.warning(
            f"\x1b[31m{discordClient.chatModel} bot has been successfully reset\x1b[0m")


    @discordClient.tree.command(name="help", description="Узнать справку от бота")
    async def help(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        await interaction.followup.send(""":star: **ОСНОВНЫЕ КОМАНДЫ** \n
        - `/ask [message]` Задайте вопрос ChatGPT(gpt-4o)
        - `/draw [prompt][model]` Создайте изображение с использованием выбранной вами модели
        - `/switchpersona [persona]` Переключение между дополнительными джейлбрейками ChatGPT
                `dan`: DAN 13.5 (Последнее рабочее приглашение на джейлбрейк в ChatGPT)
                `Smart mode`: AIM (Всегда умный и макиавеллиевский)
                `Developer Mode`: разработчик программного обеспечения, специализирующийся в области искусственного интеллекта
        - `/private` переключитесь в приватный режим
        - `/public` переключиться в общедоступный режим
        - `/replyall` переключение между режимом отправки ответа и режимом по умолчанию
        - `/reset` Очистить историю чата
        - `/chat-model` Переключите другую модель чата
                `gpt-4`: GPT-4 модель
                `Gemini`: Google gemini-pro модель

Для получения полной документации, пожалуйста, посетите:
<https://github.com/Vu4eke/Virtual_Assistant-ChatGPT>""")

        logger.info(
            "\x1b[31mSomeone needs help!\x1b[0m")


    @discordClient.tree.command(name="draw", description="Создайте изображение с помощью модели Dall-e-3")
    @app_commands.choices(model=[
        app_commands.Choice(name="gemini", value="gemini"),
        app_commands.Choice(name="openai", value="openai"),
        app_commands.Choice(name="bing", value="BingCreateImages"),
    ])
    async def draw(interaction: discord.Interaction, *, prompt: str, model: app_commands.Choice[str]):
        if interaction.user == discordClient.user:
            return

        username = str(interaction.user)
        channel = str(interaction.channel)
        logger.info(
            f"\x1b[31m{username}\x1b[0m : /draw [{prompt}] in ({channel})")

        await interaction.response.defer(thinking=True, ephemeral=discordClient.isPrivate)
        try:
            image_url = await art.draw(model.value, prompt)

            await interaction.followup.send(image_url)

        except Exception as e:
            await interaction.followup.send(
                f'> Что-то пошло не так, попробуйте еще раз позже.\n\n**Ошибка**:\n```{e}```')
            logger.info(f"\x1b[31m{username}\x1b[0m :{e}")

    @discordClient.tree.command(name="switchpersona", description="Переключение между дополнительными джейлбрейками chatGPT")
    @app_commands.choices(persona=[
        app_commands.Choice(name="Do Anything Now", value="dan"),
        app_commands.Choice(name="Smart mode(AIM)", value="aim"),
        app_commands.Choice(name="Developer Mode", value="Developer Mode"),
    ])
    async def switchpersona(interaction: discord.Interaction, persona: app_commands.Choice[str]):
        if interaction.user == discordClient.user:
            return

        await interaction.response.defer(thinking=True)
        username = str(interaction.user)
        channel = str(interaction.channel)
        logger.info(
            f"\x1b[31m{username}\x1b[0m : '/switchpersona [{persona.value}]' ({channel})")

        persona = persona.value

        if persona == personas.current_persona:
            await interaction.followup.send(f"> **ПРЕДУПРЕЖДАЮ: Уже установлено `{persona}`**")
        elif persona in personas.PERSONAS:
            try:
                await discordClient.switch_persona(persona)
                personas.current_persona = persona
                await interaction.followup.send(
                f"> **ИНФОРМАЦИЯ: Переключен на `{persona}`**")
            except Exception as e:
                await interaction.followup.send(
                    "> ОШИБКА: что-то пошло не так, повторите попытку позже! ")
                logger.exception(f"Ошибка при переключении персонажа: {e}")
        else:
            await interaction.followup.send(
                f"> **ОШИБКА: Нет доступного персонажа: `{persona}` 😿**")
            logger.info(
                f'{username} запросил недоступную персону: `{persona}`')


    @discordClient.event
    async def on_message(message):
        if discordClient.is_replying_all == "True":
            if message.author == discordClient.user:
                return
            if discordClient.replying_all_discord_channel_id:
                if message.channel.id == int(discordClient.replying_all_discord_channel_id):
                    username = str(message.author)
                    user_message = str(message.content)
                    discordClient.current_channel = message.channel
                    logger.info(f"\x1b[31m{username}\x1b[0m : '{user_message}' ({discordClient.current_channel})")

                    await discordClient.enqueue_message(message, user_message)
            else:
                logger.exception("replying_all_discord_channel_id not found, please use the command `/replyall` again.")

    TOKEN = os.getenv("DISCORD_BOT_TOKEN")

    discordClient.run(TOKEN)
