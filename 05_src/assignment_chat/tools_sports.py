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

    roster_url = f"https://api-web.nhle.com/v1/roster/{abbrev}/current"
    roster_resp = requests.get(roster_url)
    resp_dict = json.loads(roster_resp.text)

    forwards  = resp_dict.get("forwards", [])
    defense   = resp_dict.get("defensemen", [])
    goalies   = resp_dict.get("goalies", [])

    def fmt_player(p: dict) -> str:
        first = p.get("firstName", {}).get("default", "")
        last  = p.get("lastName",  {}).get("default", "")
        pos   = p.get("positionCode", "")
        num   = p.get("sweaterNumber", "?")
        return f"#{num} {first} {last} ({pos})"

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

def handle_sports_query(query: str) -> str:
    """
    Entry point called by main.py. Extracts the team name from the
    query and passes it to get_nhl_team_facts().
    """
    stop = {
        "nhl", "hockey", "team", "info", "about", "the", "tell", "me",
        "how", "is", "doing", "what", "are", "roster", "players", "who",
        "plays", "for", "give", "show", "list", "facts",
    }
    words = [w for w in query.lower().split() if w not in stop]
    team_name = " ".join(words).strip()
 
    if not team_name:
        return "Please provide an NHL team name, e.g. 'Tell me about the Toronto Maple Leafs'."
 
    return get_nhl_team_facts(team_name)
    
    
    
    #facts_list = resp_dict.get("data", [])
    
    #facts = "\n".join([f"{i+1}. {fact}\n" for i, fact in enumerate(facts_list)])
    
    #return facts

#@tool
#def get_dog_facts(n:int=1):
#    """
#    Returns n dog facts from the Dog API.
#    """
#    url = "http://dogapi.dog/api/v2/facts"
#    params = {
#        "limit": n
#    }
#    response = requests.get(url, params=params)
#    resp_dict = json.loads(response.text)
#    facts_list = resp_dict.get("data", [])
#    facts = "\n".join([f"{i+1}. {fact['attributes']['body']}\n" for i, fact in enumerate(facts_list)])
#    return facts
