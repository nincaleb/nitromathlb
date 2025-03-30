import os
import requests
import pandas as pd
from datetime import datetime
import time

# Updated TEAM_TAGS with your new teams
TEAM_TAGS = [
    "NMGDS", "X3", "FASZ", "DKC", "TOSONT", "APLU5", "EVSC", "WMDSM", "4MATH", "DM8TE",
    "FUS3", "LGCS", "PGBG", "KOTGP", "SHIP", "NFL", "CONM", "J0IN", "NMGS", "JE4US",
    "CF02", "HGWRTS", "NITR0", "CRAZZZ", "ERICK", "TRUST", "1LWS", "JLFU", "PNKYPI",
    "LEGOLF", "NFL881", "ETH", "J4UP", "TEDDY", "TCLIP", "NFO", "WCV", "BAG", "121",
    "MATT18", "ALSLUG", "SAVVEE", "BEAST", "SERVNT", "NMCH12", "MATH", "LGE", "WOLVEZ",
    "KINGS", "ZH", "JDFU", "OT", "MAHOU", "VZ", "SOW", "GHOSTS", "AMATHB", "GOAT",
    "BOB151", "ML", "CC", "WISD0M", "A298", "T2WIN", "ZWINNA", "UBL", "NMV", "N8TH",
    "1SMASH", "HIM32", "WINNR", "P0LICE", "DORYA", "ABAMS", "PRVBS", "GRIFF", "CR7TW",
    "SOCER5", "SNIPE1", "ETYPEC", "PUPBY", "RTV", "HRX", "12312B", "NTPD1", "ZOOM",
    "COBRAS", "KINGH", "R3M1X", "EASTER", "RISE", "W2V", "DRBZZZ", "81BAG", "GOLD",
    "SSA", "49ERSI", "CCFRI", "GOLD55", "GOATS", "IM2", "A3", "TMS", "TR1", "MATHNL", "JSTW", "PIGGY", "WL"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "application/json",
}

def get_team_data(team_tag, retries=3, delay=5):
    """Fetch season data and stats from the API for a team."""
    url = f"https://www.nitromath.com/api/v2/teams/{team_tag}"
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10, verify=True)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'OK':
                    season = data['results'].get('season', [])
                    stats = data['results'].get('stats', [])
                    info = data['results'].get('info', {})
                    return season, stats, info
            return [], [], {}
        except Exception as e:
            print(f"Error fetching data for team {team_tag}: {e}")
            time.sleep(delay)
    return [], [], {}

def get_team_stats(stats):
    """Extract relevant stats from the 'board: season'."""
    for stat in stats:
        if stat.get('board') == 'season':
            return {
                'answered': int(stat.get('answered', 0)),
                'played': int(stat.get('played', 0))
            }
    return {'answered': 0, 'played': 0}

# Use UTC for timestamp and filenames.
utc_timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
with open("timestamp.txt", "w") as file:
    file.write(f"Last Updated: {utc_timestamp}")

# Ensure a folder called 'csv_archive' exists
csv_archive_dir = "csv_archive"
if not os.path.exists(csv_archive_dir):
    os.makedirs(csv_archive_dir)

all_players = []
team_summary = {}  # Store team stats

for team_tag in TEAM_TAGS:
    season_data, stats_data, info_data = get_team_data(team_tag)
    if not season_data:
        print(f"No seasonal data found for team {team_tag}")
        continue

    # Extract team stats from 'board: season'
    team_stats = get_team_stats(stats_data)
    answered = team_stats['answered']
    played = team_stats['played']
    members = info_data.get('members', 0)  # Get the "members" value

    team_summary[team_tag] = {
        'Team': team_tag,
        'TotalPoints': answered,
        'Races': played,
        'Members': members  # Add the "members" value
    }

    # Process individual players
    for member in season_data:
        if member.get('points') is not None:
            username = member.get('username', 'N/A')
            display_name = member.get('displayName', 'Unknown')
            profile_link = f"https://www.nitromath.com/racer/{username}"
            points = int(member.get('points', 0))
            races = int(member.get('played', 0))

            all_players.append({
                'Username': username,
                'ProfileLink': profile_link,
                'DisplayName': display_name,
                'Races': races,
                'Points': points,
                'Team': team_tag
            })

if not all_players:
    print("No valid player data found. Please verify the team tags and API responses.")
else:
    df = pd.DataFrame(all_players)
    df = df.sort_values(by='Points', ascending=False)

    utc_filename = datetime.utcnow().strftime("%Y%m%d")
    # Save player leaderboard CSV in csv_archive folder based on UTC date.
    df.to_csv(os.path.join(csv_archive_dir, f'nitromath_season_leaderboard_{utc_filename}.csv'), index=False)

    df_teams = pd.DataFrame(list(team_summary.values()))
    df_teams = df_teams.sort_values(by='TotalPoints', ascending=False)
    # Save team leaderboard CSV in csv_archive folder based on UTC date.
    df_teams.to_csv(os.path.join(csv_archive_dir, f'nitromath_team_leaderboard_{utc_filename}.csv'), index=False)