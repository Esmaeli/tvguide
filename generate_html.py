import json
import re
import requests
import pytz
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

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

        # Get the local timezone
        local_tz = pytz.timezone('Asia/Tehran')  # Change 'Asia/Tehran' to your desired timezone
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
        channels_list += [channel['channel_name'] for channel in event['channels'].values() if isinstance(channel, dict) and 'channel_name' in channel]
    elif isinstance(event.get('channels'), list):  # If 'channels' is a list
        channels_list += [channel['channel_name'] for channel in event['channels'] if isinstance(channel, dict) and 'channel_name' in channel]
    elif isinstance(event.get('channels'), str):  # If 'channels' is a string
        channels_list.append(event['channels'])

    # Process 'channels2' field
    if isinstance(event.get('channels2'), dict):  # If 'channels2' is a dictionary
        channels_list += [channel['channel_name'] for channel in event['channels2'].values() if isinstance(channel, dict) and 'channel_name' in channel]
    elif isinstance(event.get('channels2'), list):  # If 'channels2' is a list
        channels_list += [channel['channel_name'] for channel in event['channels2'] if isinstance(channel, dict) and 'channel_name' in channel]
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
                f'<p class="time">â° {local_time}</p>'  # Display local time
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
            f'<p class="time">â° {local_time}</p>'  # Display local time
            f'<p class="channels">Channels: {", ".join(channels) if channels else "N/A"}</p>'
            f'</div>\n'
        )

    elif 'Season' in event_text or 'Episode' in event_text:  # TV Shows/Movies
        if 'Season' in event_text and 'Episode' in event_text:
            title, episode = event_text.split(', Episode')
            return (
                f'<div class="card" data-sport="{category}">'
                f'<h3>{title.strip()}</h3>'
                f'<p class="event-name">Episode {episode.strip().upper()}</p>'  # Convert episode name to uppercase
                f'<p class="time">â° {local_time}</p>'  # Display local time
                f'<p class="channels">Channels: {", ".join(channels) if channels else "N/A"}</p>'
                f'</div>\n'
            )
        else:
            return (
                f'<div class="card" data-sport="{category}">'
                f'<h3>{event_text.upper()}</h3>'  # Convert event text to uppercase
                f'<p class="event-name">{category.upper()}</p>'  # Convert category to uppercase
                f'<p class="time">â° {local_time}</p>'  # Display local time
                f'<p class="channels">Channels: {", ".join(channels) if channels else "N/A"}</p>'
                f'</div>\n'
            )

    else:  # Other events (e.g., WWE NXT) or invalid events
        return (
            f'<div class="card" data-sport="{category}">'
            f'<h3>{event_text.upper()}</h3>'  # Convert event text to uppercase
            f'<p class="event-name">{category.upper()}</p>'  # Convert category to uppercase
            f'<p class="time">â° {local_time}</p>'  # Display local time
            f'<p class="channels">Channels: {", ".join(channels) if channels else "N/A"}</p>'
            f'</div>\n'
        )

# Function to load links from a file
def load_links(file_path):
    links = {}
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
    
    matches = re.findall(r"Channel Name:\s*(.*?)\nChannel URL:\s*(.*?)\n", content)
    for name, url in matches:
        clean_name = simplify_channel_name(name)  # Ù†Ø§Ù… Ø³Ø§Ø¯Ù‡â€ŒØ´Ø¯Ù‡ Ø¨Ø±Ø§ÛŒ Ø¬Ø³ØªØ¬Ùˆ
        links[clean_name] = url
    return links

# Function to simplify channel names
def simplify_channel_name(name):
    """
    Ù†Ø§Ù… Ú©Ø§Ù†Ø§Ù„ Ø±Ø§ Ø¨Ù‡ ÙØ±Ù…Øª Ø³Ø§Ø¯Ù‡ ØªØ¨Ø¯ÛŒÙ„ Ù…ÛŒâ€ŒÚ©Ù†Ø¯ØŒ 
    ÙÙ‚Ø· Ú©Ù„Ù…Ø§Øª Ø§ØµÙ„ÛŒ Ø±Ø§ Ù†Ú¯Ù‡ Ù…ÛŒâ€ŒØ¯Ø§Ø±Ø¯ Ùˆ Ø§Ø·Ù„Ø§Ø¹Ø§Øª Ø§Ø¶Ø§ÙÛŒ Ø±Ø§ Ø­Ø°Ù Ù…ÛŒâ€ŒÚ©Ù†Ø¯.
    """
    name = name.lower()
    name = re.sub(r"(fhd|hd|sd|4k|uk|us|extra|plus|live|premium|main event)", "", name)  # Ø­Ø°Ù Ø§Ø·Ù„Ø§Ø¹Ø§Øª Ø§Ø¶Ø§ÙÛŒ
    name = re.sub(r"[^a-z0-9]+", " ", name).strip()  # Ø­Ø°Ù Ú©Ø§Ø±Ø§Ú©ØªØ±Ù‡Ø§ÛŒ Ø®Ø§Øµ
    return name

# Function to find matching channel URL
def find_matching_channel(channel_name, links):
    clean_name = simplify_channel_name(channel_name)
    
    for link_name in links:
        if clean_name in link_name:  # Ø¬Ø³ØªØ¬ÙˆÛŒ Ø³Ø§Ø¯Ù‡ Ù…Ø§Ù†Ù†Ø¯ Notepad
            return links[link_name]
    
    return None

# Function to process HTML and add links to channels
def process_html(file_path, links):
    with open(file_path, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")
    
    for p in soup.find_all("p", class_="channels"):
        new_html = []
        parts = p.text.split(", ")
        for part in parts:
            url = find_matching_channel(part, links)
            if url:
                new_html.append(f'<a href="#" class="channel-link" data-video-url="{url}">{part}</a>')
            else:
                new_html.append(part)
        p.clear()
        p.append(BeautifulSoup(", ".join(new_html), "html.parser"))
    
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(str(soup))

# Main function to process data and write to index.html
def main():
    url = "https://daddylive.mp/schedule/schedule-generated.json"
    json_data = fetch_data_from_url(url)
    if not json_data:
        print("Failed to fetch data. Exiting...")
        return

    # Define fixed categories
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

    # Ensure "TV Shows" is always the first item in More Events
    more_categories.insert(0, "TV Shows") if "TV Shows" in more_categories else more_categories.append("TV Shows")

    # Fix "Wwe" to "WWE" in primary categories
    primary_categories = [category.upper() if category.lower() == "wwe" else category.capitalize() for category in primary_categories]

    # Open the index.html file for writing
    with open('index.html', 'w', encoding='utf-8') as output_file:
        output_file.write('<!DOCTYPE html>\n<html lang="en">\n<head>\n')
        output_file.write('<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n')
        output_file.write('<title>Sportify - Your Sports Events Hub</title>\n')
        output_file.write('<link rel="stylesheet" href="styles.css">\n')
        output_file.write('<link href="https://vjs.zencdn.net/8.10.0/video-js.css" rel="stylesheet" />\n')  # Video.js CSS
        output_file.write('</head>\n<body>\n')

        # Header Section
        output_file.write('<header><div class="container"><h1>Sportify</h1>')
        output_file.write('<div class="menu-icon">â˜°</div><nav><ul class="nav-links">')

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
                # Determine the final category for this event
                final_category = category
                for fixed_category in fixed_categories[1:]:  # Skip 'all'
                    if fixed_category.lower() in category.lower():
                        final_category = fixed_category
                        break

                for event in event_list:
                    formatted_event = format_event(event, final_category.lower())
                    if formatted_event:  # Ensure the event is not None
                        output_file.write(formatted_event)

        output_file.write('</div></section></div></main>\n')

        # Footer Section
        output_file.write('<footer><div class="container"><p>&copy; 2025 Sportify. All rights reserved.</p></div></footer>\n')

        # Video Player HTML
        output_file.write('''
            <!-- Video Player -->
            <div id="videoPlayer" class="player">
                <div class="player-content">
                    <span class="close-player">&times;</span>
                    <video id="videoStream" class="video-js vjs-default-skin" controls preload="auto" width="640" height="360">
                        <source src="" type="application/x-mpegURL">
                    </video>
                </div>
            </div>
        ''')

        # JavaScript for the player
        output_file.write('''
            <script src="https://vjs.zencdn.net/8.10.0/video.min.js"></script>
            <script>
                // Get the player and video element
                const player = document.getElementById("videoPlayer");
                const videoElement = document.getElementById("videoStream");
                const closePlayerBtn = document.querySelector(".close-player");

                // Initialize Video.js player
                const videoPlayer = videojs(videoElement);

                // Function to open the player with the video URL
                function openPlayer(videoUrl) {
                    videoPlayer.src({ type: "application/x-mpegURL", src: videoUrl }); // Set the video URL
                    player.style.display = "block"; // Show the player
                    videoPlayer.play(); // Start playing the video
                }

                // Function to close the player
                function closePlayer() {
                    videoPlayer.pause(); // Pause the video
                    videoPlayer.src(""); // Clear the video source
                    player.style.display = "none"; // Hide the player
                }

                // Close the player when the user clicks on the close button
                closePlayerBtn.addEventListener("click", closePlayer);

                // Close the player when the user clicks outside of it
                window.addEventListener("click", (event) => {
                    if (event.target === player) {
                        closePlayer();
                    }
                });

                // Add click event to all channel links
                document.addEventListener("DOMContentLoaded", () => {
                    const channelLinks = document.querySelectorAll(".channels a");
                    channelLinks.forEach((link) => {
                        link.addEventListener("click", (e) => {
                            e.preventDefault(); // Prevent default link behavior
                            const videoUrl = link.getAttribute("data-video-url"); // Get the video URL
                            openPlayer(videoUrl); // Open the player with the video
                        });
                    });
                });
            </script>
        ''')

        output_file.write('</body>\n</html>')

    print("index.html has been successfully created.")

    # Process the HTML to add channel links
    links = load_links("links.txt")
    process_html("index.html", links)
    print("index.html updated with channel links!")

if __name__ == "__main__":
    main()
