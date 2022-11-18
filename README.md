# complementBot_Twitch
Make sure you have Python installed (Python 3.10.6 was used): https://www.python.org/downloads/

Make sure create a .env file in the root directory with the following variables:
- TMI_TOKEN= get your token from https://twitchapps.com/tmi/
- CLIENT_ID= register your app with twitch on https://dev.twitch.tv/console/apps/create - for name, give it the channel name (ComplementsBot in our case), OAuth Redirect URLs: https:localhost:8000, Category: Chat Bot; then go to 'Manage' and copy the Client ID 
- BOT_NICK= give it the channel name (ComplementsBot)
- BOT_PREFIX= messages beginning with this shoul be listened out for by the bot; this is usually '!'.
- CHANNEL= give it the name of the channel where you want the bot to be active
