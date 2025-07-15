# Standard Python imports
import json

# 3rd-part imports
import anthropic
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client
import asyncio

# mlbchat imports
from mlbchat.logger_config import get_logger
logger = get_logger()
from . import helpers

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
    
    try:
        # Claude credentials and settings
        claude_api_key = credentials['claude']['api_key']
        claude_version = credentials['claude']['version']
        claude_model = credentials['claude']['model']

        chatclient = anthropic.Anthropic(api_key=claude_api_key)

        response = chatclient.messages.create(
          model=claude_model,
          max_tokens=1000,
          temperature=0.15,
          messages=[
            {
              "role": "user",
              "content": [{"type": "text", "text": helpers.getBrainDeadPrompt("trades", team_name)}]
            }
          ]
        )

        return response.content[0].text
    except Exception as e:
        logger.error(str(e))
        raise Exception(str(e))

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
    
    try:
        # Claude credentials and settings
        claude_api_key = credentials['claude']['api_key']
        claude_version = credentials['claude']['version']
        claude_model = credentials['claude']['model']

        chatclient = anthropic.Anthropic(api_key=claude_api_key)

        message = chatclient.messages.create(
          model=claude_model,
          max_tokens=1000,
          temperature=0.15,
          system=helpers.getRoleBasedSystemPrompt("GM", team_name),
          messages=[
            {
              "role": "user",
              "content": [{"type": "text", "text": helpers.getRoleBasedPrompt("GM", "trades", team_name)}]
            }
          ]
        )

        return message.content[0].text
    except Exception as e:
        logger.error(str(e))
        raise Exception(str(e))

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
    
    try:
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
    except Exception as e:
        logger.error(str(e))
        raise Exception(str(e))

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
    
    try:
        response = {}
        async with sse_client(sse_endpoint) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                
                response = await session.call_tool(tool_name, tool_args)
                
        return response
    except Exception as e:
        logger.error(str(e))
        raise Exception(str(e))
    
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
    
    try:
        system_prompt = helpers.getRoleBasedSystemPrompt("GM", team_name)

        # Claude credentials and settings
        claude_api_key = credentials['claude']['api_key']
        claude_version = credentials['claude']['version']
        claude_model = credentials['claude']['model']

        chatclient = anthropic.Anthropic(api_key=claude_api_key)
        
        mcptools = asyncio.run(getToolsFromMCP(credentials['baseballmcp']['server']))
        logger.info("----------------------- Tools -------------------------")
        logger.info(str([curtool['name'] for curtool in mcptools]))
        message_traffic = [
          {
            "role": "user",
            "content": [
              {
                "type": "text",
                "text": helpers.getFirstStepToolPrompt(team_name)
              }
            ]
          }
        ]
        done = False
        queries_spent = 0
        canned_queries = 1
        while not done:
            logger.info("----------------------- Messages After " + str(queries_spent) + " Queries -------------------------")
            logger.info(json.dumps(message_traffic, indent=2))
            # Exceeded our limit?
            queries_spent += 1
            response = chatclient.messages.create(
              model=claude_model,
              max_tokens=1000,
              temperature=0.15,
              system=system_prompt,
              messages=message_traffic,
              tools=mcptools
            )
            for curContent in response.content:
                if curContent.type == 'text':
                    message_traffic.append({"role": "assistant", "content": [{"type": "text", "text": curContent.text}]})
                elif curContent.type == 'tool_use':
                    message_traffic.append({"role": "assistant", "content": [{"type": "tool_use", "name": curContent.name, "id": curContent.id, "input": curContent.input}]})
                    toolresult = asyncio.run(callMCPTool(credentials['baseballmcp']['server'], curContent.name, curContent.input))
                    response_content = []
                    for curresultcontent in toolresult.content:
                        msgdict = {"type": curresultcontent.type, "text": curresultcontent.text}
                        response_content.append(msgdict)
                    message_traffic.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": curContent.id, "content": response_content}]})
            if message_traffic[len(message_traffic) - 1]['role'] == 'assistant' and message_traffic[len(message_traffic) - 1]['content'][0]['type'] == 'text':
                if canned_queries == 1:
                    canned_queries += 1
                    message_traffic.append({"role": "user", "content": [{"type": "text", "text": helpers.getSecondStepToolPrompt(team_name)}]})
                elif canned_queries == 2:
                    canned_queries += 1
                    message_traffic.append({"role": "user", "content": [{"type": "text", "text": helpers.getThirdStepToolPrompt(team_name)}]})
                else:
                    done = True
            if queries_spent > 20:
                done = True

        logger.info("----------------------- Final Result -------------------------")
        return json.dumps(message_traffic, indent=2)
    except Exception as e:
        logger.error(str(e))
        raise Exception(str(e))
