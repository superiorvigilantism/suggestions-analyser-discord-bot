# suggestions-analyser-discord-bot
Discord.py bot that uses GPT-5.4-nano to automatically rate suggestions posted in a forum channel and promotes high-scoring suggestions to another designated channel

## Installation
1. Clone the repository:
   	```bash git clone https://github.com/superiorvigilantism/suggestions-analyser-discord-bot.git cd suggestions-analyser-discord-bot```
2. Install Python virtual environment
   	`python -m venv venv`
3. Activate venv to install requirements inside the repo
   	**On Windows:**
   	`venv\Scripts\activate`
   	**On macOS/Linux:**
   	`source venv/bin/activate`
4. Install requirements:
   	`pip install -r requirements.txt`
5. Visit Discord Developer Portal and create your application
	https://discord.com/developers/applications
	- Create a new application
	- Click on your new application in the list
	In Overview:
	- Navigate to Installation Category
	- Select Guild Install method only
	- In Default Install Settings -> Guild Install
	  Add a scope called "bot"
	  Add Permissions to:
	  1. Read Message History
	  2. Send Messages
	  3. View Channels
	Then,
	- Navigate to Bot category
	- Reset and copy the new token into your .env file
6. Visit OpenAI API Platform
	openai.com/api
	- Log in/Register
	If upon registering you were not provided an API key:
	- Navigate to API Keys
	- Create a new key/use existing one
	- Paste it into your .env file
	- On the home page, Add credits for AI to work.
	About costs: AI used in code is GPT-5.4-nano, which is currently cheapest non-deprecated model that OpenAI has to offer
7. In your Discord server,
	- Right-click your forum channel
	- Select "Copy Link"
	- From the link, copy the number located at the end starting from last slash
	- Paste the number into your .env file
	- Perform identical operation with your channel to forward worthy suggestions to
8. Run the code
	In the terminal
	- Navigate to the repo directory
	- run `python src/main.py`
	- Set a custom threshold with `!threshold <number>`
	- WARNING: As of v1.0.0 release, threshold needs to be respecified each time the bot is restarted

And thus you are set

## Usage
The bot will automatically monitor the forum, and whenever a post is made, rate it. If the score surpasses the threshold, it will be sent to your other channel, thus marking it as "worth reviewing"

### Commands
Current available commands are:
- !threshold <number>
	Sets threshold score that a suggestion must score past in order to be forwarded
- !prompt <text>
	Sets custom prompt to be used for rating suggestions
- !promptinfo
	Shows currently used prompt

## Requirements/Technology used
Refer to requirements.txt to see what technologies were used

---

This project is protected by GNU GENERAL PUBLIC LICENSE v3

2026-07-13
