# Complements Bot

## For twitch users:

I complement the sender of a message with a 3.33% (by default) chance. I currently have about 50 ways to complement you,
which you can extend yourself, or disregard completely.

Note that you might need to VIP me in your chat, especially if your viewers tend to make heavy use of the !complement
command - this is because Twitch seems to count many bot messages as spam, and mutes/times out the bot.

### Implemented commands

The following commands have been implemented:

#### Anywhere commands

The following commands work anywhere that I have joined:

- !complement \[username\] - If username present, complement that user; otherwise, get a complement yourself!

#### ComplementsBot chat only

Say these commands in my channel chat (https://www.twitch.tv/complementsbot):

- !joinme - I will join your channel
- !leaveme - I will leave your channel, but keep your settings in case you decide you want me back
- !deleteme - I will leave your channel and delete all of your settings

- !ignoreme - I will never complement you
- !unignoreme - undo !ignoreme

- !count - Check out how many channels I'm in
- !about - Learn all about me

#### Channel owner and mods only

These commands must be used by the channel owner in their own channel:

- !compleave - same as !leaveme, but you can do it in your own channel.

- !setchance - change how likely it is that person sending message gets complemented; default is 3.33%; setting it to a
  number over 100 makes it always trigger, and to 0 or less to never trigger

- !addcomplement <complement> - add a custom complement for to your own channel
- !removeallcomplements - removes all custom complements added by you
- !removecomplement <phrase> - remove a complement from your own channel; the complement which gets removed is one which contains "phrase" in it, after "phrase" has gone through the process of:
  - all non-alphanumeric (numbers and letters) characters get removed; this includes spaces
  - all letters in "phrase" get converted into lowercase
  - the resulting string (which was originally "phrase") will be compared to all custom complements with the same two things done to them, and any complement containing the phrase will be removed.
  - any removed complements will be showed in the chat
  - this might get the bot timed out/banned from your channel, especially if you are removing a lot of custom complements. Consider VIPing it if you plan on using it!

- !disablecmdcomplement - ComplementsBot will no longer send out complements when a viewer uses the !complement
  command; by default, this is off
- !enablecmdcomplement - undoes !disablecommandcomplement; this is the default
- !disablerandomcomplement - ComplementsBot will no longer send out complements randomly; by default, ComplementsBot
  does randomly send out complements
- !enablerandomcomplement - undoes !disablerandomcomplement; this is the default

- !setmutettsprefix - the character/string to put in front of a message to mute TTS (text-to-speech); default is "!"
- !mutecmdcomplement - mutes tts for complements sent with !complement command; this is the default
- !unmutecmdcomplement - undoes !mutecmdcomplement;
- !muterandomcomplement - mutes tts for complements randomly given out;
- !unmuterandomcomplement - undoes !muterandomcomplement; this is the default

- !disablecustomcomplements - I will not complement people using your own complements
- !enablecustomcomplements - I will complement people using your complements; this is the default
- !disabledefaultcomplements - I will not complement people using the default complements
- !enabledefaultcomplements - I will complement people using the default; this is the default
- !listcomplements - lists all complements which have been added; this might get the bot timed out/banned from your channel, especially if you have a lot of custom complements. Consider VIPing it if you plan on using it!

- !ignorebots - ignores users whose name ends in 'bot' for random complement (they can still be manually complemented
  using the !complement command if command complements are enabled (!enablecmdcomplement)); this is the case by default
- !unignorebots - undo ignorebots; by default, bots are ignored.

### Unimplemented commands

The following commands have not been implemented yet, but are planned to be:

#### Channel owner and mods only

These commands must be used by the channel owner in their own channel:
- !getcomplement <index> - shows you the complement of specified index number
- commands which will allow channel owners to change who can use which command (user groups would be: channel owner,
  moderators, VIPs, subscribers, regular user <- this one would allow everyone)

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
- pipenv install twitchio

Make sure create a .env file in the root directory with the following variables:

- TMI_TOKEN= get your token from https://twitchapps.com/tmi/
- CLIENT_ID= register your app with twitch on https://dev.twitch.tv/console/apps/create -
  for name, give it the channel name (ComplementsBot in our case), OAuth Redirect URLs: https:localhost:8000,
  Category: Chat Bot; then go to 'Manage' and copy the Client ID
- DATABASE_URL= the URL to your realtime database as shown in firebase

Once you have your firebase app, go to 'Service accounts' in project settings. From here, generate a new private key,
and save the file as '.firebase_config.json' in the root directory.

Create a Realtime Database in firebase with private access.
