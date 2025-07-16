# standard Python imports
import os
import csv
from collections import Counter

# 3rd-party imports
from typing import List, Optional

# mlbchat imports
from mlbchat.logger_config import get_logger
logger = get_logger()

def getBrainDeadPrompt(
    topic: str,
    team_name: str
):
    """
    Builds a very basic prompt using a topic and a team name, if relevant.
    
    Args:
        topic (str): The kind of prompt to build (trades, for example)
        team_name (str): The team involved in the prompt, if one exists
        
    Returns:
        A string prompt
        
    """
    
    if topic.lower() == 'trades':
        return "What trades should the " + team_name + " make before the deadline?"

    return ""

def getRoleBasedSystemPrompt(
    role: str,
    team_name: str
):
    """
    Builds a system prompt using a role and a team name, if relevant.
    
    Args:
        role (str): The role to build the prompt for (GM, for example)
        team_name (str): The team involved in the prompt, if one exists
        
    Returns:
        A string prompt
        
    """
    
    if role.lower() in ['gm', 'general manager']:
        return "You are the General Manager of the " + team_name + ".  You have been a baseball executive for 25 years.  Prior to that, you were a scout and involved in managing minor league teams.  Your analysis of baseball players and teams is largely based on modern statistical models.  While you are mindful of the payroll, your primary goal is to put a strong roster on the field and keep young talent within the organization."

    return ""

def getRoleBasedPrompt(
    role: str,
    topic: str,
    team_name: str
):
    """
    Builds a prompt using a role, a topic and a team name, if relevant.
    
    Args:
        role (str): The role to build the prompt for (GM, for example)
        topic (str): The kind of prompt to build (trades, for example)
        team_name (str): The team involved in the prompt, if one exists
        
    Returns:
        A string prompt
        
    """
    
    if role.lower() in ['gm', 'general manager'] and topic.lower() == 'trades':
        return "The trade deadline is coming up in the next few weeks.  Please evaluate the " + team_name + ".  What are their strengths and weaknesses?  Should they be aggressive in trades?  Please list some candidate trades involving specific players and trade partners that would be appropriate for the team in its current situation."
        
    return ""

def getFirstStepToolPrompt(
    team_name: str
):
    """
    Builds a prompt to be used as the initial prompt in an MCP exchange on trades as a GM.
    
    Args:
        team_name (str): The team involved in the prompt, if one exists
        
    Returns:
        A string prompt
        
    """
    
    return "The trade deadline is coming up in the next few weeks.  Please evaluate the " + team_name + ".  What are their strengths and weaknesses?  Should they be aggressive in trades?  If they are heading for the playoffs, what pieces would be best to focus on?  What areas could be improved for the future?  If they are likely sellers, what positions look like they could get good value back?"

def getSecondStepToolPrompt(
    team_name: str
):
    """
    Builds a prompt to be used as a follow-on prompt in an MCP exchange on trades as a GM.
    
    Args:
        team_name (str): The team involved in the prompt, if one exists
        
    Returns:
        A string prompt
        
    """
    
    return "Based on your analysis so far, please propose some specific trade candidates on the " + team_name + " and trade targets on other teams. Please verify that the trade targets are currently on the roster of the trade partners that you mention, and that the potential trade would not be rejected by the other team based on common sense."

def getThirdStepToolPrompt(
    team_name: str
):
    """
    Builds a prompt to be used as a follow-on prompt in an MCP exchange on trades as a GM.
    
    Args:
        team_name (str): The team involved in the prompt, if one exists
        
    Returns:
        A string prompt
        
    """
    
    return "Let's keep exploring other potential trade partners.  Please continue to verify that the trade targets are currently on the roster of the trade partners that you mention, and that the potential trade would not be rejected by the other team based on common sense."

def loadCSV(
    inpath: str
):
    """
    Loads the rows of a CSV file into a list of dictionaries
    with each column header as a key.

      Args:
          inpath (str): the location on disk to read the file
    """

    retdata = []
    if os.path.isfile(inpath):
        with open(inpath, 'r', encoding='utf-8') as infile:
            retdata = [{colname: str(cellvalue) for colname, cellvalue in row.items()}
                       for row in csv.DictReader(infile, skipinitialspace=True)]

    return retdata
  
def writeCSV(
    outpath: str,
    data: List,
    headers: Optional[List] = None): # type: (str, [], []) -> None
    """
    Writes a list of dictionaries to a CSV file.  Each dictionary
    must have exactly the headers as keys.

    Args:
        outpath (str): the location on disk to write the file
        data (List): the list of dictionaries that will become rows
        headers (Optional[List]): the list of column headers.  If none is provided, use the list of keys from the first dictionary in data.
    """

    useheaders = headers
    if headers is None or len(headers) == 0:
        useheaders = list(data[0].keys())

    with open(outpath, 'w', encoding='utf-8', newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=useheaders)
        writer.writeheader()
        writer.writerows(data)

def reportTradeCSV(
    inpath: str
):
    """
    Analyzes a proposed trade spreadsheet and logs various metrics
    Date,Model,Prompt Type,Focus Team,Player,For Real?,To Team,For Real?,Trade For,For Real?,Score

    Args:
        inpath (str): the location on disk to read the trade data from
    """
    
    trade_data = loadCSV(inpath)
    
    playerCounts = Counter()
    fromTeamCounts = Counter()
    toTeamCounts = Counter()
    teamCounts = Counter()
    
    for curtrade in trade_data:
        fromTeam = curtrade['Focus Team'].strip()
        if len(fromTeam) > 5:
            fromTeamCounts[fromTeam] += 1
            teamCounts[fromTeam] += 1
        fromPlayers = curtrade['Player'].split(',')
        for curPlayer in fromPlayers:
            cleanPlayer = curPlayer.strip()
            if len(cleanPlayer) > 5:
                playerCounts[cleanPlayer] += 1
        toTeam = curtrade['To Team'].strip()
        if len(toTeam) > 5:
            toTeamCounts[toTeam] += 1
            teamCounts[toTeam] += 1
        toPlayers = curtrade['Trade For'].split(',')
        for curPlayer in toPlayers:
            cleanPlayer = curPlayer.strip()
            if len(cleanPlayer) > 5:
                playerCounts[cleanPlayer] += 1
        
    logger.info("Teams: ")
    logger.info(str(teamCounts.most_common()))
    logger.info("From Teams: ")
    logger.info(str(fromTeamCounts.most_common()))
    logger.info("To Teams: ")
    logger.info(str(toTeamCounts.most_common()))
    logger.info("Players: ")
    logger.info(str(playerCounts.most_common()))
    
    
