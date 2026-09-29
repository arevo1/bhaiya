# bhaiya — recipe-link Discord bot

A small Discord bot that collects cooking-recipe links shared from social media and recommends a random one when you ask.

- Post a link from Instagram, YouTube / Shorts, TikTok, Facebook, Pinterest, X/Twitter or Reddit and the bot saves it to `recipes.txt`.
- Type `!bolo` and the bot suggests a random saved recipe.

## Setup

### 1. Create the bot in the Discord Developer Portal

1. Go to <https://discord.com/developers/applications> and click **New Application**.
2. Open the **Bot** tab, click **Reset Token**, and copy the token. Keep it secret.
3. On the same **Bot** tab, under **Privileged Gateway Intents**, turn on **Message Content Intent** and save. Without it the bot can't read links in messages.

### 2. Invite the bot to your server

1. Open **OAuth2 → URL Generator**.
2. Under **Scopes**, tick `bot`.
3. Under **Bot Permissions**, tick:
   - Read Messages / View Channels
   - Send Messages
   - Add Reactions
   - Read Message History
4. Open the generated URL and add the bot to your server.

### 3. Install and configure

Requires Python 3.10+.

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # Windows: copy .env.example .env
```

Edit `.env` and set your token:

```
DISCORD_TOKEN=your_token_here
```

`.env` is in `.gitignore`. Never commit it.

## Run

```bash
python bot.py
```

The console logs startup and every saved recipe.

## Usage

Save a recipe with a name (any text that isn't a URL becomes the name):

```
https://www.instagram.com/reel/xyz Paneer Butter Masala
```

Save a recipe without a name (stored as `Untitled`):

```
https://youtu.be/abc123
```

The bot reacts with ✅ and replies `Saved: Paneer Butter Masala`. If a message has several links, each one is saved separately with the same name. A link that is already saved is skipped, and the bot replies that it's already there.

Get a random recommendation:

```
!bolo
```

```
Try this: **Paneer Butter Masala** — https://www.instagram.com/reel/xyz (shared by username)
```

## Storage format

Recipes are appended to `recipes.txt` next to `bot.py` (created automatically, UTF-8, never rewritten). One entry per line:

```
2026-09-29T14:32:10 | username | Paneer Butter Masala | https://www.instagram.com/reel/xyz
```

Any `|` characters in recipe names are removed so the file stays easy to parse.
