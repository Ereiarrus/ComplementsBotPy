# Complements Bot

## For twitch users:

I complement the sender of a message with a 3.33% (by default) chance. I currently have about 50 ways to complement you,
which you can extend yourself, or disregard completely.

Note that you might need to VIP me in your chat, especially if your viewers tend to make heavy use of the !complement
command - this is because Twitch seems to count many bot messages as spam, and mutes/times out the bot.

If, for whatever reason, you decide to change your Twitch username, know that the bot will NOT be in your chat if you don't take action.
You will have to come into the bot's channel chat and type !refresh. MAKE SURE you run the !refresh command after changing your username,
as if you change your username a second time without having run the !refresh command after the first time you changed it, you will not be
able to get the bot to join your chat on your own (i.e. you will have to contact me and get me to run the !refreshall command)

#### Anywhere commands

The following commands work anywhere that I have joined:

- !complement \[username\] - If username present, complement that user; otherwise, get a complement yourself!

- !compignoreme - I will stop complementing you (see !ignoreme in '[ComplementsBot chat only](#ComplementsBot chat only)'); note that this command gives no feedback whether it was successful
- !compunignoreme - undo !compignoreme/!ignoreme (see in '[ComplementsBot chat only](#ComplementsBot chat only)'); note that this command gives no feedback whether it was successful

#### ComplementsBot chat only

Say these commands in my channel chat (https://www.twitch.tv/complementsbot):

- !joinme - I will join your channel
- !leaveme - I will leave your channel, but keep your settings in case you decide you want me back
- !deleteme - I will leave your channel and delete all of your settings; this does not affect your ignored status, 
so if you did !ignoreme, I will still know that you don't want to be complemented after doing !deleteme, and your 
twitch username/user id will still be stored in my database. If you don't want this, then also do !unignore me - 
this will remove any reference of you from my database
- !refresh - When you change your Twitch username, you must make use of this, as otherwise the bot might not join your (new) chat (unless/when I restart it) (**NOT WORKING YET**)
- !refreshall - (NOT AVAILABLE TO GENERAL PUBLIC due to potentially high overhead) refreshes the full list of joined channels, and joins renamed users' (new) chats (**NOT WORKING YET**)

- !ignoreme - I will stop complementing you
- !unignoreme - undo !ignoreme

- !count - Check out how many channels I'm in
- !about - Learn all about me

#### Channel owner and mods only

These commands must be used by the channel owner in their own channel:

- !compleave/!compleaveme - same as !leaveme, but you can do it in your own channel.

- !setchance - change how likely it is that person sending message gets complemented; default is 3.33%; setting it to a
  number over 100 makes it always trigger, and to 0 or less to never trigger

- !addcomplement/!addcomp <complement> - add a custom complement for to your own channel
- !removeallcomplements/!removeallcomps - removes all custom complements added by you
- !removecomplement/!removecomp <phrase> - remove a complement from your own channel; the complement which gets removed is one which contains "phrase" in it, after "phrase" has gone through the process of:
  - all non-alphanumeric (numbers and letters) characters get removed; this includes spaces
  - all letters in "phrase" get converted into lowercase
  - the resulting string (which was originally "phrase") will be compared to all custom complements with the same two things done to them, and any complement containing the phrase will be removed.
  - any removed complements will be showed in the chat
  - this might get the bot timed out/banned from your channel, especially if you are removing a lot of custom complements. Consider VIPing it if you plan on using it!
  - **Example usage**: say that one of your custom complements is "You arw an awful person!"; you can remove this by typing '!removecomp youar wa', assuming no other custom complements contain the phrase 'youarwa' after having gone through the above process.

- !disablecmdcomplement/!disablecommandcomplement/!disablecommandcomp/!disablecmdcomp - 
ComplementsBot will no longer send out complements when a viewer uses the !complement command; by default, this is off
- !enablecmdcomplement/!enablecommandcomplement/!enablecommandcomp/!enablecmdcomp - undoes !disablecommandcomplement; 
this is the default
- !disablerandomcomplement/!disablerandcomplement/!disablerandcomp/!disablerandomcomp - ComplementsBot will no longer 
send out complements randomly; by default, ComplementsBot does randomly send out complements
- !enablerandomcomplement/!enablerandcomplement/!enablerandcomp/!enablerandomcomp - undoes !disablerandomcomplement; 
this is the default

- !setmutettsprefix - the character/string to put in front of a message to mute TTS (text-to-speech); default is "!"
- !mutecmdcomplement/!mutecommandcomplement/!mutecommandcomp/!mutecmdcomp - mutes tts for complements sent with !complement command; this is the default
- !unmutecmdcomplement/!unmutecommandcomplement/!unmutecommandcomp/!unmutecmdcomp - undoes !mutecmdcomplement;
- !muterandomcomplement/!muterandcomplement/!muterandcomp/!muterandomcomp - mutes tts for complements randomly given out;
- !unmuterandomcomplement/!unmuterandcomplement/!unmuterandcomp/!unmuterandomcomp - undoes !muterandomcomplement; this is the default

- !disablecustomcomplements/!disablecustomcomps - I will not complement people using your own complements
- !enablecustomcomplements/!enablecustomcomps - I will complement people using your complements; this is the default
- !disabledefaultcomplements/!disabledefaultcomps - I will not complement people using the default complements
- !enabledefaultcomplements/!enabledefaultcomps - I will complement people using the default; this is the default
- !listcomplements/!listcomps - lists all complements which have been added; this might get the bot timed out/banned 
from your channel, especially if you have a lot of custom complements. Consider VIPing it if you plan on using it!

- !ignorebots/!ignorebot - ignores users whose name ends in 'bot' for random complement (they can still be manually complemented
  using the !complement command if command complements are enabled (!enablecmdcomplement)); this is the case by default
- !unignorebots/!unignorebot - undo ignorebots; by default, bots are ignored.

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

Make sure create a .env file in the src directory with the following variables:

- TMI_TOKEN= get your token from https://twitchapps.com/tmi/
- DATABASE_URL= the URL to your realtime database as shown in firebase
- CLIENT_SECRET= go to https://dev.twitch.tv/console/apps, click 'Manage', and generate a 'New Secret'.

Also, create a .env file in the root directory with:

- DEFINITELY_GITHUB_SECRET= generate a cryptographically secure random string, e.g. using 'secrets' module in python.

(alternatively, you can set these as environment variables, and do export for each one: 
`export TMI_TOKEN; export DATABASE_URL; export CLIENT_SECRET; export DEFINITELY_GITHUB_SECRET`).

Also put these environment variables as repository secrets on GitHub, and either as a file or environment variables on your server

Once you have your firebase app, go to 'Service accounts' in project settings. From here, generate a new private key,
and save the file as '.firebase_config.json' in the src directory.

Create a Realtime Database in firebase with private access.


set up SSH key on server:
	- ssh-keygen -t ed25519 -C "<your GitHub email here>"
	- eval `ssh-agent -s`
	- ssh-add ~/.ssh/id_ed25519
	- cat ~/.ssh/id_ed25519.pub
	- paste public key into github https://github.com/settings/keys: new SSH key

### Running program on a VPS

- git pull the repository
- make sure python is installed (ideally with the same version as used for the program, in this case 3.10.6); also ensure pip was installed with it
- install requirements: python3 -m pip install -r requirements.txt
- make .env and .firebase_config files to match your local ones (NEVER PUSH THEM TO GITHUB!)
- start up the program either directly in the background: `python3 main.py > /dev/null 2>&1 &`, or as a daemon: `setsid python3 main.py >/dev/null 2>&1 < /dev/null &`


### Setting up CI/CD with Docker instead

This is the better option than just running it directly.

Mostly following instructions from https://docs.docker.com/engine/install/centos/ and https://docs.docker.com/engine/install/linux-postinstall/ in this part 

First, we have to make a clean installation of Docker on the server (example is for CentOS):

- `sudo yum remove docker docker-client docker-client-latest docker-common docker-latest docker-latest-logrotate docker-logrotate docker-engine`
- `sudo yum install -y yum-utils`
- `sudo yum install -y docker-compose`
- `sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo`
- `sudo yum install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y` - If prompted to accept the GPG key, verify that the fingerprint matches 060A 61C5 1B55 8A7F 742B 77AA C52F EB6B 621E 9F35, and if so, accept it.
- `sudo systemctl start docker`
- verify it works using `sudo docker run hello-world`

Add user to the docker usergroup:
- `sudo groupadd docker` - create it in case it doesn't exist
- possibly need to `rm -rf ~/.docker`
- `sudo usermod -aG docker <username>`, and relog into account

Start docker on boot:
- `sudo systemctl enable docker.service`
- `sudo systemctl enable containerd.service`

Or to disable it on boot:
- `sudo systemctl disable docker.service`
- `sudo systemctl disable containerd.service`

Docker makes log files that could get out of hand (https://docs.docker.com/config/containers/logging/json-file/)

in /etc/docker, create a daemon.json file with contents:
`{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "30m",
    "max-file": "3" 
  }
}`

Docker has to be restarted before these changes take place; existing containers do not use the new config.

Finally, to start the app (i.e. run the container):
- `docker run --log-driver json-file --log-opt max-size=30m --log-opt max-file=3 complements-bot-py`

Here I make use of in-line logging alterations `--log-driver json-file --log-opt max-size=30m --log-opt max-file=3`.










