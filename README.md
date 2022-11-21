# complementBot_Twitch

## For twitch users:

I complement the sender of a message with a 3.33% chance. I currently have about 50 ways to complement you. 

### Implemented commands

The following commands have been implemented:

#### ComplementsBot chat only

Say these commands in my channel chat here:
- !count - Check out how many channels I'm in

#### Anywhere commands

The following commands work anywhere that I have joined:
- !complement \[username\] - If username present, complement that user; otherwise, get a complement yourself!

### Unimplemented commands

The following commands have not been implemented yet, but are planned to be:

#### ComplementsBot chat only

Say these commands in my channel chat here:
- !joinme - I will join your channel
- !leaveme - I will leave your channel
- !about - Learn all about me
- !ignoreme - I will never complement you
- !unignoreme - undo !ignoreme

#### Channel owner only

These commands work in any channel I'm in, but must be used by the channel owner:
- !setchance - change how likely it is that person sending message gets complemented; default is 3.33%
- !addcomplement <complement> - add a custom complement for to your own channel
- !removecomplement <complement> - remove a complement from your own channel
- !listcomplements - lists all complements which have been added
- !setmutettsprefix - the character/string to put in front of a message to mute tts; default is "!"
- !mutecmdcomplement - mutes tts for complements sent with !complement command; 
can either be 'true' or 'false', default is 'true'
- !muterandcomplement - mutes tts for complements randomly given out; can either be 'true' 
or 'false', default is 'false'

## About bot and me

Twitch channel: https://www.twitch.tv/complementsbot

Also check out https://www.twitch.tv/ereiarrus (if I ever decide to stream...)

YouTube channel: https://www.youtube.com/channel/UChejDismPBRIXFUNC-hB_bQ

Donations to my PayPal are appreciated, but never necessary: me.he.jey+ereiarrus@gmail.com

## For developers:

I followed https://dev.to/ninjabunny9000/let-s-make-a-twitch-bot-with-python-2nd8 to get started, 
along with looking at https://github.com/TwitchIO/TwitchIO for examples to build upon:

- Make sure you have Python installed (Python 3.10.6 was used): https://www.python.org/downloads/
- Run pipenv: pipenv --python 3.10
- pipenv install twitchio json

Make sure create a .env file in the root directory with the following variables:
- TMI_TOKEN= get your token from https://twitchapps.com/tmi/
- CLIENT_ID= register your app with twitch on https://dev.twitch.tv/console/apps/create - 
for name, give it the channel name (ComplementsBot in our case), OAuth Redirect URLs: https:localhost:8000, 
Category: Chat Bot; then go to 'Manage' and copy the Client ID
- CHANNELS= give it the name of the channel where you want the bot to be active, separated by colons (':')
- IGNORED_USERS= List of ignored users, separated by colons
