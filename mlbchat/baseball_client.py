# Standard Python imports
import json

# 3rd-part imports
import anthropic
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client
import asyncio

def simpleton_trade(
    team_name: str,
    credentials: dict
):
    """
    Asks Claude about what trades a team should make, using no tools or system prompts.
    Intended to be a "Worst Case Scenario" of using an LLM.
    
    Args:
        team_name (str): The team name, such as "Washington Nationals"
        credentials (dict): Credentials necessary to access the Claude LLM
    
    Returns:
        str: Claude's response contents
    """
    
    # Claude credentials and settings
    claude_api_key = credentials['api_key']
    claude_version = credentials['version']
    claude_model = credentials['model']

    chatclient = anthropic.Anthropic(api_key=claude_api_key)

    response = chatclient.messages.create(
      model=claude_model,
      max_tokens=1000,
      temperature=0.15,
      messages=[
        {
          "role": "user",
          "content": [{"type": "text", "text": "What trades should the " + team_name + " make before the deadline?"}]
        }
      ]
    )

    return response.content[0].text

def role_based_trade(
    team_name: str,
    credentials: dict
):
    """
    Asks Claude about what trades a team should make, using a role-based system prompt.
    Intended to be acting as an MLB General Manager.
    
    Args:
        team_name (str): The team name, such as "Washington Nationals"
        credentials (dict): Credentials necessary to access the Claude LLM
    
    Returns:
        str: Claude's response contents
    """
    
    # Claude credentials and settings
    claude_api_key = credentials['api_key']
    claude_version = credentials['version']
    claude_model = credentials['model']

    chatclient = anthropic.Anthropic(api_key=claude_api_key)

    message = chatclient.messages.create(
      model=claude_model,
      max_tokens=1000,
      temperature=0.15,
      system="You are the General Manager of the " + team_name + ".  You have been a baseball executive for 25 years.  Prior to that, you were a scout and involved in managing minor league teams.  Your analysis of baseball players and teams is largely based on modern statistical models.  While you are mindful of the payroll, your primary goal is to put a strong roster on the field and keep young talent within the organization.",
      messages=[
        {
          "role": "user",
          "content": [{"type": "text", "text": "The trade deadline is coming up in the next few weeks.  Please evaluate the " + team_name + ".  What are their strengths and weaknesses?  Should they be aggressive in trades?  Please list some candidate trades involving specific players and trade partners that would be appropriate for the team in its current situation."}]
        }
      ]
    )

    return message.content[0].text

async def getToolsFromMCP(
    sse_endpoint: str
):
    """
    Obtains a list of tools, descriptions and input schemata from an SSE MCP server
    
    Args:
        sse_endpoint (str): the MCP endpoint to interrogate
      
    Returns:
      dict: the tools, their descriptions and their output schemata
    
    """
    
    rettools = []
    async with sse_client(sse_endpoint) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            
            tools = await session.list_tools()
            for curtool in tools.tools:
                tooldict = {}
                tooldict['name'] = curtool.name
                tooldict['description'] = curtool.description
                tooldict['input_schema'] = curtool.inputSchema
                rettools.append(tooldict)
                
    return rettools

async def callMCPTool(
    sse_endpoint: str,
    tool_name: str,
    tool_args: dict
):
    """
    Calls an MCP server to execute a named tool with given arguments
    
    Args:
        sse_endpoint (str): the MCP endpoint to interrogate
        tool_name (str): the name of the tool to call
        tool_args (dict): the request message for the tool
      
    Returns:
      dict: the tool response
    
    """
    
    response = {}
    async with sse_client(sse_endpoint) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            
            response = await session.call_tool(tool_name, tool_args)
            
    return response
    
def tools_trade(
    team_name: str,
    credentials: dict
):
    """
    Asks Claude about what trades a team should make, using a role-based system prompt and a local MCP server for baseball stats.
    Intended to be acting as an MLB General Manager augmented by real-time statistics.
    
    Args:
        team_name (str): The team name, such as "Washington Nationals"
        credentials (dict): Credentials necessary to access the Claude LLM
    
    Returns:
        str: Claude's response contents
    """
    
    system_prompt = "You are the General Manager of the " + team_name + ".  You have been a baseball executive for 25 years.  Prior to that, you were a scout and involved in managing minor league teams.  Your analysis of baseball players and teams is largely based on modern statistical models.  While you are mindful of the payroll, your primary goal is to put a strong roster on the field and keep young talent within the organization."

    # Claude credentials and settings
    claude_api_key = credentials['api_key']
    claude_version = credentials['version']
    claude_model = credentials['model']

    chatclient = anthropic.Anthropic(api_key=claude_api_key)
    
    mcptools = asyncio.run(getToolsFromMCP("http://localhost:8080/mcp"))
    print("----------------------- Tools -------------------------")
    print(str([curtool['name'] for curtool in mcptools]))
    message_traffic = [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": "The trade deadline is coming up in the next few weeks.  Please evaluate the " + team_name + ".  What are their strengths and weaknesses?  Should they be aggressive in trades?  Please list some candidate trades involving specific players and trade partners that would be appropriate for the team in its current situation."
          }
        ]
      }
    ]
    done = False
    queries_spent = 0
    while not done:
        print("----------------------- Messages -------------------------")
        print(json.dumps(message_traffic, indent=2))
        queries_spent += 1
        response = chatclient.messages.create(
          model=claude_model,
          max_tokens=1000,
          temperature=0.15,
          system=system_prompt,
          messages=message_traffic,
          tools=mcptools
        )
        print("LLM Responded with " + str(len(response.content)) + " answers")
        # Exceeded our limit
        if queries_spent > 10:
            done = 1
        # Regular text response, nothing fancy - if it asks about looking up more specifics, respond yes, otherwise terminate
        elif response.content[0].type == 'text' and len(response.content) == 1:
            message_traffic.append({"role": "assistant", "content": [{"type": "text", "text": response.content[0].text}]})
            msgtext = response.content[0].text.lower()
            if 'look up specific players' in msgtext or 'would you like me to' in msgtext or 'you would like me to' in msgtext:
                message_traffic.append({"role": "user", "content": [{"type": "text", "text": "Yes, please give me more specifics on which players are good trade candidates, and which trade partners might be interested in them."}]})
            else:
                done = 1
        # Might want a tool call
        else:
            for curcontent in response.content:
                if curcontent.type == 'text':
                    message_traffic.append({"role": "assistant", "content": [{"type": "text", "text": curcontent.text}]})
                elif curcontent.type == 'tool_use':
                    message_traffic.append({"role": "assistant", "content": [{"type": "tool_use", "name": curcontent.name, "id": curcontent.id, "input": curcontent.input}]})
#                    print("----------------------- Tool Call Request ------------------------")
#                    print(curcontent.name)
#                    print(json.dumps(curcontent.input, indent=2))
                    toolresult = asyncio.run(callMCPTool("http://localhost:8080/mcp", curcontent.name, curcontent.input))
#                    print("----------------------- Tool Call Result -------------------------")
                    msgcontent = []
                    for curresultcontent in toolresult.content:
                        msgdict = {"type": curresultcontent.type, "text": curresultcontent.text}
                        msgcontent.append(msgdict)
#                    print(json.dumps(msgcontent, indent=2))
                    message_traffic.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": curcontent.id, "content": msgcontent}]})

    print("----------------------- Final Result -------------------------")
    return json.dumps(message_traffic, indent=2)
