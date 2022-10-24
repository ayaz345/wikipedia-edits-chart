import requests
import calendar
from datetime import datetime, timedelta
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/{username}", response_class=HTMLResponse)
async def get_user(
    request: Request, username: str, language: str,
    year: str, appearance: str = "light"
    ):
    r_url = f"https://{language}.wikipedia.org/w/api.php"
    r_params = {
        "action": "query",
        "format": "json",
        "list": "usercontribs",
        "uclimit": 500,  # maximum allowed to request
        "ucuser": username,
        "ucstart": f"{year}-12-31T00:00:00Z",
        "ucend": f"{year}-01-01T00:00:00Z"
    }

    colour_mode = f"/{appearance}.css"

    # Request and save the data
    response = None
    try:
        response = requests.get(url=r_url, params=r_params).json()
    except:
        print("The user couldn't be found.")

    if len(response["query"]["usercontribs"]) == 0:
        return templates.TemplateResponse(
            "nodata.html",
            {
                "request": request,
                "data": "<p id=\"not-found\">No data was found for this user for this period of time.</p>",
            }
        )

    contrib_days = {}
    while True:
        for contribution in response["query"]["usercontribs"]:
            date = contribution["timestamp"][:10]

            if date not in contrib_days.keys():
                contrib_days[date] = 1
            else:
                contrib_days[date] = contrib_days[date] + 1

        if "continue" not in response:
            break

        r_params["uccontinue"] = response["continue"]["uccontinue"]
        response = requests.get(url=r_url, params=r_params).json()

    # Calculate longest and current streak
    total_contribs = sum(contrib_days.values())
    streak_number = 0
    streak_contribs = ""

    if year == str(datetime.now().year):
        last = datetime.now()
        while True:
            yesterday = last - timedelta(days=1)
            if str(yesterday)[:10] in contrib_days:
                streak_number += 1
                last = yesterday
            else:
                break

        streak_contribs = f"Current streak: {streak_number}"
    else:
        streak_count = 0
        last = datetime.strptime(list(contrib_days.keys())[0], "%Y-%m-%d")
        for day in range(len(list(contrib_days.keys()))):
            if str(last)[:10] in contrib_days:
                last = last - timedelta(days=1)
                streak_count += 1

                if (streak_number < streak_count):
                    streak_number = streak_count
            else:
                last = datetime.strptime(list(contrib_days.keys())[day], "%Y-%m-%d") - timedelta(days=1)
                streak_count = 1

        streak_contribs = f"Longest streak: {streak_number}"

    # Calculate total number of edits made in the year
    max_contrib = max(contrib_days.values())
    day_levels = []
    last_number = max_contrib
    for _ in range(5):
        last_number = last_number - (max_contrib / 6)
        day_levels.append(int(last_number))

    # Format the data using HTML
    contrib_data = ""

    year_days = calendar.Calendar().yeardayscalendar(int(year), width=12)
    
    month_names = {
        1: "January", 2: "February", 3: "March",
        4: "April", 5: "May", 6: "June",
        7: "July", 8: "August", 9: "September",
        10: "October", 11: "November", 12: "December"
    }
    month_count = 1
    for month in year_days[0]:
        lower_month = month_names[month_count].lower()

        contrib_data += f"<div id=\"{lower_month}\" class=\"month\">"
        contrib_data += f"<h2 class=\"month-title\">{month_names[month_count]}</h2>"
        contrib_data += "<div class=\"month-container\">"

        week_count = 1
        for week in month:
            contrib_data += f"<div id=\"{lower_month}-week-{week_count}\" class=\"week\">"

            for day in week:
                number_day = f"{year}-{str(month_count).zfill(2)}-{str(day).zfill(2)}"
                char_day = f"{month_names[month_count][:3]} {day}, {year}"

                day_transparency = "no-transparent"
                contrib_level = "day-level-0"
                tooltip = f"No contributions on {char_day}"

                if day == 0:
                    day_transparency = "yes-transparent"
                    contrib_level = ""
                    tooltip = ""

                if number_day in contrib_days:
                    tooltip = f"{contrib_days[number_day]} contributions on {char_day}"

                    if contrib_days[number_day] >= day_levels[0]:
                        contrib_level = "day-level-6"
                    elif contrib_days[number_day] >= day_levels[1]:
                        contrib_level = "day-level-5"
                    elif contrib_days[number_day] >= day_levels[2]:
                        contrib_level = "day-level-4"
                    elif contrib_days[number_day] >= day_levels[3]:
                        contrib_level = "day-level-3"
                    elif contrib_days[number_day] >= day_levels[4]:
                        contrib_level = "day-level-2"
                    elif contrib_days[number_day] < day_levels[4] and contrib_days[number_day] > 1:
                        contrib_level = "day-level-1"
                    elif contrib_days[number_day] == 1:
                        contrib_level = "day-level-1"
                        tooltip = f"{contrib_days[number_day]} contribution on {char_day}"

                contrib_data += f"""
                <div class=\"day {contrib_level} {day_transparency}\">
                    <span class=\"tooltip-text\">{tooltip}</span>
                </div>
                """

            contrib_data += "</div>"
            week_count += 1

        contrib_data += "</div>"
        contrib_data += "</div>"
        month_count += 1

    return templates.TemplateResponse(
        "userchart.html",
        {
            "request": request,
            "year": year,
            "username": username,
            "data": contrib_data,
            "appearance": colour_mode,
            "total": total_contribs,
            "streak": streak_contribs
        }
    )