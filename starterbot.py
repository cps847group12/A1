#Adopted with modifications from https://github.com/mattmakai/slack-starterbot/blob/master/starterbot.py
#Distributed under MIT license

#don't forget to set the environmental variable SLACK_BOT_TOKEN using
#export SLACK_BOT_TOKEN=xoxb
#or hardcode 

import os
import time
import re
import requests
import json
import enchant
from slackclient import SlackClient

import json #used for debug printing


# instantiate Slack client
slack_client = SlackClient('TOKEN-303510733220-I75yLw2RojwlZ9srQuWwdWL0')
# starterbot's user ID in Slack: value is assigned after the bot starts up
starterbot_id = None

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
ECHO_COMMAND = "echo"
WEATHER_COMMAND = "weather"
MENTION_REGEX = "^<@(|[WU].+)>(.*)"

def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        #uncomment line below to debug print
        #print json.dumps(event, indent = 2, sort_keys = True)
        
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            #uncomment line below to debug print
            #print user_id, " : ", message
            if user_id == starterbot_id:
                return message, event["channel"]
    return None, None

def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def handle_command(command, channel):
    """
        Executes bot command if the command is known
    """
    # Default response is help text for the user
    default_response = "Not sure what you mean. Try *{}* or *{} (city)*.".format(ECHO_COMMAND, WEATHER_COMMAND)

    # Finds and executes the given command, filling in response
    response = None
    
    if command.startswith(ECHO_COMMAND):
        if len(ECHO_COMMAND)==len(command):
           response="Sure...I need some text to do that!"
        else:
           response=command[command.index(ECHO_COMMAND) + len(ECHO_COMMAND) + 1:]
    
    elif command.startswith(WEATHER_COMMAND):
        if len(WEATHER_COMMAND)==len(command):
           response="Sure...I need a city to do that!"      
        else:
           dictionary = enchant.request_pwl_dict("cities.txt")
           suggestion=dictionary.suggest(command[command.index(WEATHER_COMMAND) + len(WEATHER_COMMAND) + 1:])
           requestget = requests.get('http://api.openweathermap.org/data/2.5/weather?q=' + suggestion[0].replace(" ", "%20") + '&units=metric&appid=bbb393e2a17ca6ff2a90939e14b836e2')
           if requestget.status_code == 200:
                 responsedata=requestget.json()
                 response = 'Today\'s weather for: ' + responsedata['name'] + ', ' + responsedata['sys']['country'] + '\nDescription: ' + responsedata['weather'][0]['main'] + ', ' + responsedata['weather'][0]['description'] + '\nTemperature in Celsius: ' + "{0:.2f}".format(responsedata['main']['temp']) + '\nMinimum Temperature in Celsius: ' + "{0:.2f}".format(responsedata['main']['temp_min']) + '\nMaximum Temperature in Celsius: ' + "{0:.2f}".format(responsedata['main']['temp_max']) + '\nHumidity: ' + str(responsedata['main']['humidity']) + '%\nWind: ' + "{0:.2f}".format(responsedata['wind']['speed']) + ' meters/sec'
           else:
              response="Unfortunately...I do not recognize the city"                   
    
    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response
    )

if __name__ == "__main__":
    # avm: connect is designed for larger teams, 
    # see https://slackapi.github.io/python-slackclient/real_time_messaging.html
    # for details
    if slack_client.rtm_connect(with_team_state=False):
        print("Starter Bot connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        starterbot_id = slack_client.api_call("auth.test")["user_id"]
        while True:
            command, channel = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, channel)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")
