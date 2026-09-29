"""Discord bot that collects recipe links from social media and recommends a random one."""

import logging
import os
import random
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import discord
from discord.ext import commands
from dotenv import load_dotenv

RECIPES_FILE = Path(__file__).resolve().parent / "recipes.txt"
SEPARATOR = " | "
UNTITLED = "Untitled"

# Domains treated as recipe sources (subdomains such as www., m., vm. also match).
SOCIAL_DOMAINS = {
    "instagram.com",
    "youtube.com",
    "youtu.be",
    "tiktok.com",
    "facebook.com",
    "fb.com",
    "fb.watch",
    "pinterest.com",
    "pin.it",
    "x.com",
    "twitter.com",
    "reddit.com",
    "redd.it",
}

URL_PATTERN = re.compile(r"https?://[^\s<>]+", re.IGNORECASE)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("recipe-bot")


def extract_urls(text: str) -> list[str]:
    """Return all http(s) URLs in the text, with trailing punctuation removed."""
    return [url.rstrip(".,!?;:)]}>'\"") for url in URL_PATTERN.findall(text)]


def is_social_url(url: str) -> bool:
    """True if the URL's host is one of the supported social/video platforms."""
    try:
        host = (urlparse(url).hostname or "").lower()
    except ValueError:
        return False
    return any(host == domain or host.endswith("." + domain) for domain in SOCIAL_DOMAINS)


def extract_name(text: str) -> str:
    """Everything in the message that is not a URL, cleaned up for storage."""
    name = URL_PATTERN.sub(" ", text).replace("|", " ")
    name = " ".join(name.split())
    return name or UNTITLED


def parse_line(line: str) -> dict | None:
    """Parse a stored line into its fields, or None if it is malformed."""
    line = line.strip()
    if not line:
        return None
    try:
        rest, url = line.rsplit(SEPARATOR, 1)
        timestamp, username, name = rest.split(SEPARATOR, 2)
    except ValueError:
        return None
    return {"timestamp": timestamp, "username": username, "name": name, "url": url}


def load_recipes() -> list[dict]:
    """Read all recipes from the file. Returns an empty list if missing or unreadable."""
    if not RECIPES_FILE.exists():
        return []
    try:
        with RECIPES_FILE.open("r", encoding="utf-8") as f:
            return [entry for entry in map(parse_line, f) if entry]
    except OSError as exc:
        log.error("Could not read %s: %s", RECIPES_FILE, exc)
        return []


def is_duplicate(url: str, saved_urls: set[str]) -> bool:
    return url in saved_urls


def append_recipe(username: str, name: str, url: str) -> bool:
    """Append one recipe line to the file. Returns True on success."""
    timestamp = datetime.now().isoformat(timespec="seconds")
    line = SEPARATOR.join([timestamp, username.replace("|", " "), name, url])
    try:
        with RECIPES_FILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError as exc:
        log.error("Could not write to %s: %s", RECIPES_FILE, exc)
        return False
    log.info("Saved recipe from %s: %s -> %s", username, name, url)
    return True


def pick_random_recipe() -> dict | None:
    recipes = load_recipes()
    return random.choice(recipes) if recipes else None


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    log.info("Logged in as %s (id: %s)", bot.user, bot.user.id)
    log.info("Recipes file: %s", RECIPES_FILE)


@bot.command(name="bolo")
async def bolo(ctx: commands.Context):
    """Recommend a random saved recipe."""
    recipe = pick_random_recipe()
    if recipe is None:
        await ctx.reply("No recipes saved yet! Share a recipe link and I'll remember it. 🍳")
        return
    await ctx.reply(
        f"Try this: **{recipe['name']}** — {recipe['url']} (shared by {recipe['username']})"
    )


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # Commands (e.g. !bolo) are never saved as recipes.
    if message.content.strip().startswith(bot.command_prefix):
        await bot.process_commands(message)
        return

    urls = [url for url in extract_urls(message.content) if is_social_url(url)]
    if not urls:
        return

    name = extract_name(message.content)
    saved_urls = {entry["url"] for entry in load_recipes()}
    saved, duplicates, failed = [], [], []

    for url in dict.fromkeys(urls):  # de-duplicate within the message, keep order
        if is_duplicate(url, saved_urls):
            duplicates.append(url)
        elif append_recipe(message.author.name, name, url):
            saved.append(url)
            saved_urls.add(url)
        else:
            failed.append(url)

    lines = []
    if saved:
        lines.append(f"Saved: {name}" + (f" ({len(saved)} links)" if len(saved) > 1 else ""))
    for url in duplicates:
        lines.append(f"Already saved: <{url}>")
    if failed:
        lines.append("Sorry, I couldn't save that right now. Please try again later.")

    try:
        if saved:
            await message.add_reaction("✅")
        await message.reply("\n".join(lines), mention_author=False)
    except discord.HTTPException as exc:
        log.warning("Could not respond to message %s: %s", message.id, exc)


def main():
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise SystemExit("DISCORD_TOKEN is not set. Copy .env.example to .env and add your token.")
    bot.run(token, log_handler=None)


if __name__ == "__main__":
    main()
