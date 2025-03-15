import requests
import pytz
from datetime import datetime, timedelta
from tzlocal import get_localzone  # Import get_localzone from tzlocal

# Function to fetch data from the internet
def fetch_data_from_url(url):
@@ -28,8 +27,8 @@ def convert_to_local_time(uk_time_str):
# Assume UK is UTC+0
utc_time = pytz.utc.localize(datetime.combine(datetime.today(), uk_time.time()))

        # Get the local timezone of the user's system
        local_tz = get_localzone()  # Use tzlocal to get the system's local timezone
        # Get the local timezone
        local_tz = pytz.timezone('Asia/Tehran')  # Change 'Asia/Tehran' to your desired timezone
local_time = utc_time.astimezone(local_tz)

# Return only the time in HH:MM format
@@ -38,39 +37,23 @@ def convert_to_local_time(uk_time_str):
print(f"Error converting time: {e}")
return uk_time_str  # Return original time if conversion fails

# Function to extract channels from event data and create hyperlinks
# Function to extract channels from event data
def extract_channels(event):
channels_list = []

# Process 'channels' field
if isinstance(event.get('channels'), dict):  # If 'channels' is a dictionary
        for channel in event['channels'].values():
            if isinstance(channel, dict) and 'channel_name' in channel and 'channel_id' in channel:
                channel_name = channel['channel_name']
                channel_id = channel['channel_id']
                channels_list.append(f'<a href="#" onclick="openStream(\'{channel_id}\')" style="color: blue; text-decoration: none;">{channel_name}</a>')
        channels_list += [channel['channel_name'] for channel in event['channels'].values() if isinstance(channel, dict) and 'channel_name' in channel]
elif isinstance(event.get('channels'), list):  # If 'channels' is a list
        for channel in event['channels']:
            if isinstance(channel, dict) and 'channel_name' in channel and 'channel_id' in channel:
                channel_name = channel['channel_name']
                channel_id = channel['channel_id']
                channels_list.append(f'<a href="#" onclick="openStream(\'{channel_id}\')" style="color: blue; text-decoration: none;">{channel_name}</a>')
        channels_list += [channel['channel_name'] for channel in event['channels'] if isinstance(channel, dict) and 'channel_name' in channel]
elif isinstance(event.get('channels'), str):  # If 'channels' is a string
channels_list.append(event['channels'])

# Process 'channels2' field
if isinstance(event.get('channels2'), dict):  # If 'channels2' is a dictionary
        for channel in event['channels2'].values():
            if isinstance(channel, dict) and 'channel_name' in channel and 'channel_id' in channel:
                channel_name = channel['channel_name']
                channel_id = channel['channel_id']
                channels_list.append(f'<a href="#" onclick="openStream(\'{channel_id}\')" style="color: blue; text-decoration: none;">{channel_name}</a>')
        channels_list += [channel['channel_name'] for channel in event['channels2'].values() if isinstance(channel, dict) and 'channel_name' in channel]
elif isinstance(event.get('channels2'), list):  # If 'channels2' is a list
        for channel in event['channels2']:
            if isinstance(channel, dict) and 'channel_name' in channel and 'channel_id' in channel:
                channel_name = channel['channel_name']
                channel_id = channel['channel_id']
                channels_list.append(f'<a href="#" onclick="openStream(\'{channel_id}\')" style="color: blue; text-decoration: none;">{channel_name}</a>')
        channels_list += [channel['channel_name'] for channel in event['channels2'] if isinstance(channel, dict) and 'channel_name' in channel]
elif isinstance(event.get('channels2'), str):  # If 'channels2' is a string
channels_list.append(event['channels2'])

@@ -124,6 +107,27 @@ def format_event(event, category):
f'</div>\n'
)

    elif 'Season' in event_text or 'Episode' in event_text:  # TV Shows/Movies
        if 'Season' in event_text and 'Episode' in event_text:
            title, episode = event_text.split(', Episode')
            return (
                f'<div class="card" data-sport="{category}">'
                f'<h3>{title.strip()}</h3>'
                f'<p class="event-name">Episode {episode.strip().upper()}</p>'  # Convert episode name to uppercase
                f'<p class="time">⏰ {local_time}</p>'  # Display local time
                f'<p class="channels">Channels: {", ".join(channels) if channels else "N/A"}</p>'
                f'</div>\n'
            )
        else:
            return (
                f'<div class="card" data-sport="{category}">'
                f'<h3>{event_text.upper()}</h3>'  # Convert event text to uppercase
                f'<p class="event-name">{category.upper()}</p>'  # Convert category to uppercase
                f'<p class="time">⏰ {local_time}</p>'  # Display local time
                f'<p class="channels">Channels: {", ".join(channels) if channels else "N/A"}</p>'
                f'</div>\n'
            )

else:  # Other events (e.g., WWE NXT) or invalid events
return (
f'<div class="card" data-sport="{category}">'
@@ -134,28 +138,6 @@ def format_event(event, category):
f'</div>\n'
)

# Function to prioritize Soccer events based on keywords
def prioritize_soccer_events(events):
    # List of keywords for prioritization
    keywords = [
        "England", "Spain", "Italy", "France", "Germany", 
        "Bundesliga", "Saudi Arabia", "Saudi", "Arabia", "Turkey"
    ]

    # Separate events into prioritized and non-prioritized
    prioritized_events = []
    non_prioritized_events = []

    for event in events:
        event_text = event.get('event', '').lower()
        if any(keyword.lower() in event_text for keyword in keywords):
            prioritized_events.append(event)
        else:
            non_prioritized_events.append(event)

    # Combine the lists with prioritized events first
    return prioritized_events + non_prioritized_events

# Main function to process data and write to index.html
def main():
url = "https://daddylive.mp/schedule/schedule-generated.json"
@@ -188,48 +170,18 @@ def main():
# Capitalize multi-part categories (e.g., "Water Sport" -> "Water Sport")
more_categories = [category.title() for category in more_categories]

    # Ensure "TV Shows" is always the first item in More Events
    more_categories.insert(0, "TV Shows") if "TV Shows" in more_categories else more_categories.append("TV Shows")

# Fix "Wwe" to "WWE" in primary categories
primary_categories = [category.upper() if category.lower() == "wwe" else category.capitalize() for category in primary_categories]

# Open the index.html file for writing
with open('index.html', 'w', encoding='utf-8') as output_file:
        # Write HTML document
output_file.write('<!DOCTYPE html>\n<html lang="en">\n<head>\n')
output_file.write('<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n')
output_file.write('<title>Sportify - Your Sports Events Hub</title>\n')
        output_file.write('<link rel="stylesheet" href="styles.css">\n')

        # Add inline styles
        output_file.write('<style>\n')
        output_file.write('.stream-window {\n')
        output_file.write('    display: none;\n')
        output_file.write('    position: fixed;\n')
        output_file.write('    top: 0;\n')
        output_file.write('    left: 0;\n')
        output_file.write('    width: 100%;\n')
        output_file.write('    height: 100%;\n')
        output_file.write('    background-color: rgba(0, 0, 0, 0.8);\n')
        output_file.write('    z-index: 1000;\n')
        output_file.write('}\n')
        output_file.write('.stream-content {\n')
        output_file.write('    position: absolute;\n')
        output_file.write('    top: 50%;\n')
        output_file.write('    left: 50%;\n')
        output_file.write('    transform: translate(-50%, -50%);\n')
        output_file.write('    width: 80%;\n')
        output_file.write('    height: 80%;\n')
        output_file.write('}\n')
        output_file.write('.close-button {\n')
        output_file.write('    position: absolute;\n')
        output_file.write('    top: 10px;\n')
        output_file.write('    right: 10px;\n')
        output_file.write('    color: white;\n')
        output_file.write('    font-size: 20px;\n')
        output_file.write('    cursor: pointer;\n')
        output_file.write('}\n')
        output_file.write('</style>\n')

        output_file.write('</head>\n<body>\n')
        output_file.write('<link rel="stylesheet" href="styles.css">\n</head>\n<body>\n')

# Header Section
output_file.write('<header><div class="container"><h1>Sportify</h1>')
@@ -255,52 +207,22 @@ def main():
# Traverse the JSON structure and assign events to appropriate categories
for date, events in json_data.items():
for category, event_list in events.items():
                # Skip TV Shows category entirely
                if "TV Shows" in category:
                    continue

# Determine the final category for this event
final_category = category
for fixed_category in fixed_categories[1:]:  # Skip 'all'
if fixed_category.lower() in category.lower():
final_category = fixed_category
break

                # Prioritize Soccer events
                if final_category.lower() == "soccer":
                    event_list = prioritize_soccer_events(event_list)

for event in event_list:
formatted_event = format_event(event, final_category.lower())
if formatted_event:  # Ensure the event is not None
output_file.write(formatted_event)

output_file.write('</div></section></div></main>\n')

        # Stream Window
        output_file.write('<div id="streamWindow" class="stream-window">\n')
        output_file.write('    <div class="stream-content">\n')
        output_file.write('        <span class="close-button" onclick="closeStream()">×</span>\n')
        output_file.write('        <iframe id="streamFrame" class="video responsive" marginheight="0" marginwidth="0" src="" name="iframe_a" scrolling="no" allowfullscreen="yes" width="100%" height="100%" frameborder="0">Your Browser Do not Support Iframe</iframe>\n')
        output_file.write('    </div>\n')
        output_file.write('</div>\n')

# Footer Section
output_file.write('<footer><div class="container"><p>&copy; 2025 Sportify. All rights reserved.</p></div></footer>\n')

        # Add JavaScript
        output_file.write('<script>\n')
        output_file.write('function openStream(channelId) {\n')
        output_file.write('    var streamUrl = "https://daddylive.mp/embed/stream-" + channelId + ".php";\n')
        output_file.write('    document.getElementById("streamFrame").src = streamUrl;\n')
        output_file.write('    document.getElementById("streamWindow").style.display = "block";\n')
        output_file.write('}\n')
        output_file.write('function closeStream() {\n')
        output_file.write('    document.getElementById("streamWindow").style.display = "none";\n')
        output_file.write('    document.getElementById("streamFrame").src = ""; // Clear the iframe source\n')
        output_file.write('}\n')
        output_file.write('</script>\n')

output_file.write('<script src="script.js"></script>\n</body>\n</html>')

print("index.html has been successfully created.")
