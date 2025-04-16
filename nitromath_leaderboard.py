import os
import json
import time
import pandas as pd
from datetime import datetime, timezone

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

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
    "SSA", "49ERSI", "CCFRI", "GOLD55", "GOATS", "IMT", "A3", "TMS", "TR1", "MATHNL",
    "JSTW", "PIGGY", "WL", "IM4", "TIKTOK", "CC1", "404", "LORD", "SPILA", "DVM",
    "GO10"
]
TEAM_TAGS = sorted(list(set(TEAM_TAGS)), key=TEAM_TAGS.index)

# --- Selenium Setup (optimized + explicit binary) ---
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-logging")
chrome_options.add_argument("--log-level=3")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_experimental_option("prefs", {
    "profile.managed_default_content_settings.images": 2
})
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
)
chrome_options.set_capability("pageLoadStrategy", "eager")

# point at system installed chrome & chromedriver
chrome_options.binary_location = os.getenv(
    "CHROME_BINARY",
    "/usr/bin/chromium-browser"
)
driver_service = Service(executable_path=os.getenv(
    "CHROMEDRIVER_PATH",
    "/usr/bin/chromedriver"
))
driver = webdriver.Chrome(service=driver_service, options=chrome_options)
driver.set_page_load_timeout(10)

def get_team_data(driver, team_tag, retries=3, delay=2):
    url = f"https://www.nitromath.com/api/v2/teams/{team_tag}"
    for attempt in range(1, retries+1):
        try:
            print(f"[{team_tag}] fetching (attempt {attempt})")
            driver.get(url)
            time.sleep(0.5)
            try:
                raw = driver.find_element(By.TAG_NAME, "pre").text
            except:
                raw = driver.find_element(By.TAG_NAME, "body").text
            data = json.loads(raw)
            if data.get("status") == "OK":
                return (
                    data["results"].get("season", []),
                    data["results"].get("stats", []),
                    data["results"].get("info", {})
                )
            print(f"[{team_tag}] status: {data.get('status')}")
            return [], [], {}
        except TimeoutException:
            print(f"[{team_tag}] load timed out")
            return [], [], {}
        except Exception as e:
            print(f"[{team_tag}] error: {e}, retrying in {delay}s")
            time.sleep(delay)
    return [], [], {}

def get_team_stats(stats):
    for stat in stats:
        if stat.get("board") == "season":
            return {
                "answered": int(stat.get("answered", 0)),
                "played":   int(stat.get("played",   0)),
                "errs":     int(stat.get("errs",     0))
            }
    return {"answered":0,"played":0,"errs":0}

def calculate_points(answered, errs, played):
    return (answered - errs) / played if played > 0 else 0

# timestamp
utc_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
with open("timestamp.txt","w") as f:
    f.write(f"Last Updated: {utc_ts}")

csv_archive_dir = "csv_archive"
os.makedirs(csv_archive_dir, exist_ok=True)

all_players = []
team_summary = {}

for tag in TEAM_TAGS:
    season_data, stats_data, info_data = get_team_data(driver, tag)
    if not season_data:
        print(f"[{tag}] no data")
        continue

    ts = get_team_stats(stats_data)
    pts = calculate_points(ts["answered"], ts["errs"], ts["played"])
    members = info_data.get("members", 0)

    team_summary[tag] = {
        "Team":        tag,
        "TotalPoints": ts["answered"] - ts["errs"],
        "Races":       ts["played"],
        "Members":     members
    }

    for m in season_data:
        if m.get("points") is None:
            continue
        answered = int(m.get("answered", 0))
        played   = int(m.get("played",   0))
        errs     = int(m.get("errs",     0))
        title    = m.get("title", "N/A")
        pts_p    = answered - errs if played > 0 else 0

        all_players.append({
            "Username":    m.get("username","N/A"),
            "ProfileLink": f"https://www.nitromath.com/racer/{m.get('username','')}",
            "DisplayName": m.get("displayName","Unknown"),
            "Races":       played,
            "Points":      pts_p,
            "Title":       title,
            "Team":        tag
        })

if all_players:
    df = pd.DataFrame(all_players).sort_values("Points", ascending=False)
    stamp = datetime.utcnow().strftime("%Y%m%d")
    df.to_csv(os.path.join(csv_archive_dir, f'nitromath_season_leaderboard_{stamp}.csv'), index=False)

    df2 = pd.DataFrame(team_summary.values()).sort_values("TotalPoints", ascending=False)
    df2.to_csv(os.path.join(csv_archive_dir, f'nitromath_team_leaderboard_{stamp}.csv'), index=False)
else:
    print("No valid player data found.")

driver.quit()
