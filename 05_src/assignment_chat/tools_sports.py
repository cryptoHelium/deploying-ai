# Service 1 API Call
# This service will retrieve NHL team info using the free NHL API
# To keep it simple we will only retrieve team information. I could not get other things to work.
# You specify an NHL team and it will return basic info about the team and the current roster.
# We have to parse through the response and present it to the model


# Note: there are two API calls.
# Call #1 takes the name of the team and finds the abbreviation. The API isnt based on the full team name
# Call #2 then it uses the abbreviation to make a call to the api to get the current roster information
# We split the roster information into forwards, defensement and goalies. It gets returned as a numbered list

from langchain.tools import tool
import json
import requests


@tool
def get_nhl_team_facts(team_name: str = "Toronto Maple Leafs") -> str:
    """
    Get NHL team info. NHL is the National Hockey League
    """
    url = "https://api.nhle.com/stats/rest/en/team"
    
    teams_response = requests.get(url)
    
    teams_data = json.loads(teams_response.text)

    abbrev = None
 
    query = team_name.lower().strip()

    for team in teams_data.get("data", []):
        full_name    = team.get("fullName", "").lower()
        common_name  = team.get("commonName", "").lower()
        tricode      = team.get("triCode", "")
        if query in full_name or query in common_name or full_name in query:
            abbrev = tricode
            break

    if not abbrev:
        return f"Could not find an NHL team matching '{team_name}'. Check the spelling and try again."


    #Now that we have the abbr. get the team information

    roster_url = f"https://api-web.nhle.com/v1/roster/{abbrev}/current"
    roster_resp = requests.get(roster_url)
    resp_dict = json.loads(roster_resp.text)

    # we need to split everything to make it clean

    forwards  = resp_dict.get("forwards", [])
    defense   = resp_dict.get("defensemen", [])
    goalies   = resp_dict.get("goalies", [])

    def fmt_player(p: dict) -> str:
        first = p.get("firstName", {}).get("default", "")
        last  = p.get("lastName",  {}).get("default", "")
        pos   = p.get("positionCode", "")
        num   = p.get("sweaterNumber", "?")
        return f"#{num} {first} {last} ({pos})"

   #this will be used by the model and returned back to the user
   
    facts_list = [
        f"Team: {team_name}  (abbreviation: {abbrev})",
        f"Total forwards: {len(forwards)}",
        f"Total defensemen: {len(defense)}",
        f"Total goalies: {len(goalies)}",
        f"Forwards: {', '.join(fmt_player(p) for p in forwards)}",
        f"Defensemen: {', '.join(fmt_player(p) for p in defense)}",
        f"Goalies: {', '.join(fmt_player(p) for p in goalies)}",
    ]

    facts = "\n".join([f"{i+1}. {fact}\n" for i, fact in enumerate(facts_list)])
    return facts