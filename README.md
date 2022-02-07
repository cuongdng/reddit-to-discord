# Reddit To Discord Bot
[Invite bot](https://top.gg/bot/921685959345586206) (You don't need to do anything)
-
A discord bot, when it is invoked, it will take a random post from any Subreddit that you setup before. Then send to your channel.

## Installation
### 01. Edit Config
rename config_sample.cfg -> config.cfg and edit config file:

```bash
[Reddit]
# https://www.reddit.com/prefs/apps
client_id=YOUR_CLIENT_ID
client_secret=YOUR_CLIENT_SECRET
user_agent=YOUR_USER_AGENT
password=YOUR_REDDIT_PASSWORD
username=YOUR_REDDIT_USERNAME

[Discord]
# https://discordapp.com/developers/applications/me
discord_token=YOUR_DISCORD_TOKEN
owner_id=YOUR_DISCORD_PROFILE_ID

[postgreSQL]
database=YOUR_DATABASE_NAME
user=YOUR_DATABASE_USERNAME
password=YOUR_DATABASE_PASSWORD
host=YOUR_DATABASE_HOST_ADDRESS
```
You can search on Internet how to get these information.

### 02. Database:
I'm using PostgreSQL to this project. I recommend using it, otherwise you will have to change a bit of how database query. Database has only 1 table name "subreddit" with three columns: "subreddit", "keyword", "guild_list".

### 03. Install all package on  requirements.


## Usage
### Directly use Bot without doing anything: [Invite bot](https://top.gg/bot/921685959345586206)
---
Invite your bot to your server. Run bot on your computer or you can host on any server that will let the bot run 24/7. I'm using Heroku.
```python
python bot.py
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
## Support
Email: cuongdn.sun@gmail.com