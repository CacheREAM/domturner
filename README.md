# Dominions Turner

A Discord bot written in Python that automatically scrapes blitzserver for game information

# Commands
?unchecked - Retrieves the last set of scraped data for the channel it is invoked in  
?bind **url**, **role mention** - Binds the channel the command was invoked in to a URL and role mention  
?unbind - Unbinds the channel the command was invoked in, and erases all saved data for that channel from the database  
?forcescrape - Scrapes the URL bound to the channel the command was invoked in and saves the data to the json  
?adduser **id**, **user mention** - Binds the ID of the nation to a user, so they can be mentioned by the autochecker  
?deluser **id** - Removes the user attached to a nation ID  
?set_minutes_per_check **minutes** - Sets how often the autochecker scrapes blitzserver for game info, in minutes  
?set_min_unready_before_warn **minimum** - Modifies how many users need to be unready before the autochecker warns the channel  
?set_min_time_before_warn **minutes** - Modifies how many minutes there need to be left in a turn before the autochecker warns the channel  
?toggle_emoji_mode - Will toggle emojis in the unchecked output  
?toggle_autocheck - Turns the autochecker on for the channel it is invoked in and immediately begins the scraping at intervals set by set_minutes_per_check  
?view_options - DMs you the options for the channel it is invoked in  
