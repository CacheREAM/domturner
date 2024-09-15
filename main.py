from config import TOKEN
from logger import get_logger
from commands import bot

logger = get_logger()


# Event to log commands
@bot.event
async def on_command(ctx):
    logger.info(f"Command '{ctx.command}' ran by user {ctx.author} with ID {
                ctx.author.id} at {ctx.message.created_at}")


# Run the bot
bot.run(TOKEN)
