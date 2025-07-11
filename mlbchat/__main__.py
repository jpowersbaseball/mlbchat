# Base Python imports
import logging
import argparse
import datetime
import sys
import os
import json

# 3rd-party imports
import anthropic
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client
import asyncio

# mlbchat imports
import mlbchat.baseball_client as bc

# Get a list of current Claude models: https://docs.anthropic.com/en/docs/about-claude/models/overview

async def minimal_example():
    """Ultra-minimal example - direct usage"""
    
    async with sse_client("http://localhost:8080/mcp") as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            
            tools = await session.list_tools()
#            print("Tools:", [tool.name for tool in tools.tools])
            print("Tools:", str(tools.tools))

def main(): # type: () -> None
    logging.basicConfig(format='%(asctime)-15s %(message)s', level=logging.ERROR)
    leParser = argparse.ArgumentParser()
    leParser.add_argument('--operation', help='What do you want MLB chat to do? (test|trades)')
    leParser.add_argument('--config', help='A JSON file with settings, credentials, etc.')
    leParser.add_argument('--team', help='A Major League Baseball team, for example: Washington Nationals')
    lesArgs = leParser.parse_args()
  
    if not hasattr(lesArgs, 'operation') or lesArgs.operation is None:
        logging.error('MLB chat needs to know what to do.')
        leParser.print_help()
        sys.exit(2)
  
    configs = {}
    if hasattr(lesArgs, 'config') and lesArgs.config is not None:
        with open(lesArgs.config, "r") as f:
            configs = json.load(f)
  
    if lesArgs.operation == 'test':
        if 'claude' not in configs:
            logging.error('No credential found for Claude')
            sys.exit(2)
        claude_api_key = configs['claude']['api_key']
        claude_version = configs['claude']['version']
        claude_model = configs['claude']['model']
        chatclient = anthropic.Anthropic(api_key=claude_api_key)
        message = chatclient.messages.create(
          model=claude_model,
          max_tokens=1000,
          temperature=0.15,
          system="You are a motivational speaker. You travel the country telling audiences how they should live their lives.",
          messages=[
            {
              "role": "user",
              "content": [{"type": "text", "text": "How can a person live a good life?"}]
            }
          ]
        )
        print(message.content[0].text)
        
    if lesArgs.operation == 'trades' and hasattr(lesArgs, 'team') and 'claude' in configs:
        print('================ Simpleton ==================')
        print(bc.simpleton_trade(lesArgs.team, configs['claude']))
        print('================ Role-based ==================')
        print(bc.role_based_trade(lesArgs.team, configs['claude']))
        print('================ Tool-use ==================')
        print(bc.tools_trade(lesArgs.team, configs['claude']))

    if lesArgs.operation == 'testmcp':
        asyncio.run(minimal_example())

if __name__ == '__main__':
  main()
