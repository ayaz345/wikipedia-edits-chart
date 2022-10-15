import requests
import pandas as pd
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()


@app.get("/{username}", response_class=HTMLResponse)
async def get_user(username: str, language: str, year: str):
    URL = f"https://{language}.wikipedia.org/w/api.php"
    PARAMS = {
        "action": "query",
        "format": "json",
        "list": "usercontribs",
        "uclimit": 500,  # maximum allowed to request
        "ucuser": username
    }

    response = None
    try:
        response = requests.get(url=URL, params=PARAMS).json()
    except:
        print("The user couldn't be found.")

    contrib_days = {}
    for contribution in response["query"]["usercontribs"]:
        date = contribution["timestamp"][:10]

        if date not in contrib_days.keys():
            contrib_days[date] = 1
        else:
            contrib_days[date] = contrib_days[date] + 1

    year_days = pd.date_range(f"{year}-01-01", f"{year}-12-31")

    contrib_data = ""


    for day in year_days:
        contrib_data += f"<p></p>"

    return f"""
    <body>
        <h1>Year: {year}. Contributions from user {username}</h1>
        <div id="contribution-chart">
            {contrib_days}
        </div>
    </body>
    """