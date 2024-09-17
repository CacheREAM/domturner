from keys import TOKEN
from logger import get_logger
from commands import bot
from autocheck import start_autocheck

logger = get_logger()


# Event to log commands
@bot.event
async def on_command(ctx):
    logger.info(f"Command '{ctx.command}' ran by user {ctx.author} with ID {
                ctx.author.id} at {ctx.message.created_at}")


# Start autocheck when the bot is ready
@bot.event
async def on_ready():
    await start_autocheck()


# Run the bot
bot.run(TOKEN)
