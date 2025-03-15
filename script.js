import json
import re
import requests
import pytz
from datetime import datetime
from tzlocal import get_localzone  # Import get_localzone from tzlocal

# Function to fetch data from the internet
def fetch_data_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes
        return response.json()  # Parse JSON data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return None

# Function to convert UK time to local user time
def convert_to_local_time(uk_time_str):
    try:
        if not uk_time_str or uk_time_str == 'N/A':  # Check for empty or invalid time
            return 'N/A'

        # Define UK time format and parse the input string
        uk_time_format = "%H:%M"
        uk_time = datetime.strptime(uk_time_str, uk_time_format)

        # Assume UK is UTC+0
        utc_time = pytz.utc.localize(datetime.combine(datetime.today(), uk_time.time()))

        # Get the local timezone of the user's system
        local_tz = get_localzone()  # Use tzlocal to get the system's local timezone
        local_time = utc_time.astimezone(local_tz)

        # Return only the time in HH:MM format
        return local_time.strftime("%H:%M")
    except Exception as e:
        print(f"Error converting time: {e}")
        return uk_time_str  # Return original time if conversion fails

# Function to extract channels from event data
def extract_channels(event):
    channels_list = []

    # Process 'channels' field
    if isinstance(event.get('channels'), dict):  # If 'channels' is a dictionary
        for channel in event['channels'].values():
            if isinstance(channel, dict) and 'channel_name' in channel:
                channel_name = channel['channel_name']
                channels_list.append(channel_name)
    elif isinstance(event.get('channels'), list):  # If 'channels' is a list
        for channel in event['channels']:
            if isinstance(channel, dict) and 'channel_name' in channel:
                channel_name = channel['channel_name']
                channels_list.append(channel_name)
    elif isinstance(event.get('channels'), str):  # If 'channels' is a string
        channels_list.append(event['channels'])

    # Process 'channels2' field
    if isinstance(event.get('channels2'), dict):  # If 'channels2' is a dictionary
        for channel in event['channels2'].values():
            if isinstance(channel, dict) and 'channel_name' in channel:
                channel_name = channel['channel_name']
                channels_list.append(channel_name)
    elif isinstance(event.get('channels2'), list):  # If 'channels2' is a list
        for channel in event['channels2']:
            if isinstance(channel, dict) and 'channel_name' in channel:
                channel_name = channel['channel_name']
                channels_list.append(channel_name)
    elif isinstance(event.get('channels2'), str):  # If 'channels2' is a string
        channels_list.append(event['channels2'])

    return channels_list

# Function to detect the type of event and format it for HTML
def format_event(event, category):
    event_text = event.get('event', '')  # Use .get() to avoid KeyError
    time = event.get('time', 'N/A')  # Provide a default value if 'time' is missing

    # Extract channels from the event
    channels = extract_channels(event)

    # Convert UK time to local time
    local_time = convert_to_local_time(time)

    # Detect the type of event (using Regular Expression)
    if ':' in event_text and re.search(r'\b(vs|\.vs|x)\b', event_text, re.IGNORECASE):  # Sporting event with two teams
        event_parts = event_text.split(':')
        category_name = event_parts[0].strip()
        teams_part = event_parts[1].strip()

        # Extract Team 1 and Team 2 using Regular Expression
        match = re.search(r'(.+?)\s*(vs|\.vs|x)\s*(.+)', teams_part, re.IGNORECASE)
        if match:
            team_1 = match.group(1).strip()
            team_2 = match.group(3).strip()
            return (
                f'<div class="card" data-sport="{category}">'
                f'<h3>{category_name}</h3>'
                f'<div class="teams">'
                f'<span class="team-left">{team_1}</span>'
                f'<span class="vs">vs</span>'
                f'<span class="team-right">{team_2}</span>'
                f'</div>'
                f'<p class="time">⏰ {local_time}</p>'  # Display local time
                f'<p class="channels">Channels: {", ".join(channels) if channels else "N/A"}</p>'
                f'</div>\n'
            )

    elif ':' in event_text and not re.search(r'\b(vs|\.vs|x)\b', event_text, re.IGNORECASE):  # Single sporting event
        event_parts = event_text.split(':')
        category_name = event_parts[0].strip()
        single_event = event_parts[1].strip()
        return (
            f'<div class="card single-event" data-sport="{category}">'
            f'<h3>{category_name}</h3>'
            f'<p class="event-name">{single_event.upper()}</p>'  # Convert single events to uppercase
            f'<p class="time">⏰ {local_time}</p>'  # Display local time
            f'<p class="channels">Channels: {", ".join(channels) if channels else "N/A"}</p>'
            f'</div>\n'
        )

    else:  # Other events (e.g., WWE NXT) or invalid events
        return (
            f'<div class="card" data-sport="{category}">'
            f'<h3>{event_text.upper()}</h3>'  # Convert event text to uppercase
            f'<p class="event-name">{category.upper()}</p>'  # Convert category to uppercase
            f'<p class="time">⏰ {local_time}</p>'  # Display local time
            f'<p class="channels">Channels: {", ".join(channels) if channels else "N/A"}</p>'
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
    json_data = fetch_data_from_url(url)
    if not json_data:
        print("Failed to fetch data. Exiting...")
        return

    # Define fixed categories (TV Shows removed)
    fixed_categories = ['all', 'Soccer', 'Volleyball', 'Basketball', 'Handball', 'Tennis', 'Hockey', 'Cricket', 'Boxing', 'WWE']

    # Extract all unique categories from the JSON data
    all_categories = sorted(set([category for date, events in json_data.items() for category in events.keys()]))

    # Separate fixed categories and more categories
    primary_categories = fixed_categories.copy()  # Start with fixed categories
    more_categories = []

    for category in all_categories:
        if category not in fixed_categories:
            # Check if the category is a subcategory of any fixed category
            matched = False
            for fixed_category in fixed_categories[1:]:  # Skip 'all'
                if fixed_category.lower() in category.lower():
                    matched = True
                    break
            if not matched:
                more_categories.append(category)

    # Capitalize multi-part categories (e.g., "Water Sport" -> "Water Sport")
    more_categories = [category.title() for category in more_categories]

    # Fix "Wwe" to "WWE" in primary categories
    primary_categories = [category.upper() if category.lower() == "wwe" else category.capitalize() for category in primary_categories]

    # Open the index.html file for writing
    with open('index.html', 'w', encoding='utf-8') as output_file:
        # Write HTML document
        output_file.write('<!DOCTYPE html>\n<html lang="en">\n<head>\n')
        output_file.write('<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n')
        output_file.write('<title>Sportify - Your Sports Events Hub</title>\n')
        output_file.write('<link rel="stylesheet" href="styles.css">\n')
        output_file.write('</head>\n<body>\n')

        # Header Section
        output_file.write('<header><div class="container"><h1>Sportify</h1>')
        output_file.write('<div class="menu-icon">☰</div><nav><ul class="nav-links">')

        # Write primary categories to the navigation menu
        for category in primary_categories:
            output_file.write(f'<li><a href="#" data-sport="{category.lower()}">{category}</a></li>\n')

        # Add "More Events" dropdown if there are more categories
        if more_categories:
            output_file.write('<li class="dropdown"><a href="#" class="dropbtn">More Events</a>')
            output_file.write('<div class="dropdown-content">\n')
            for category in more_categories:
                output_file.write(f'<a href="#" data-sport="{category.lower()}">{category}</a>\n')
            output_file.write('</div></li>')

        output_file.write('</ul><div class="search-box"><input type="text" id="searchInput" placeholder="Search events..."></div></nav></div></header>\n')

        # Main Content Section
        output_file.write('<main><div class="container"><section id="events"><h2>Today\'s Events</h2><div class="event-cards">\n')

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

        # Footer Section
        output_file.write('<footer><div class="container"><p>&copy; 2025 Sportify. All rights reserved.</p></div></footer>\n')

        # Add JavaScript for search functionality
        output_file.write('<script>\n')
        output_file.write('document.getElementById("searchInput").addEventListener("input", function() {\n')
        output_file.write('    const searchTerm = this.value.toLowerCase();\n')
        output_file.write('    const cards = document.querySelectorAll(".card");\n')
        output_file.write('    cards.forEach(card => {\n')
        output_file.write('        const eventText = card.textContent.toLowerCase();\n')
        output_file.write('        if (eventText.includes(searchTerm)) {\n')
        output_file.write('            card.style.display = "block";\n')
        output_file.write('        } else {\n')
        output_file.write('            card.style.display = "none";\n')
        output_file.write('        }\n')
        output_file.write('    });\n')
        output_file.write('});\n')
        output_file.write('</script>\n')

        output_file.write('</body>\n</html>')

    print("index.html has been successfully created.")

if __name__ == "__main__":
    main()
