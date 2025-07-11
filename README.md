# Model Context Protocol Client for MLB Data

This module implements an MCP Client that asks an Anthropic LLM -
[Claude Haiku 3.5](https://www.anthropic.com/claude/haiku) is the assumption -
to provide trade recommendations for a Major League Team.  It is designed to
work with the [MCP Potluck Server] (https://github.com/jpowersbaseball/mcppotluck),
but could likely get interesting results with any baseball statistics tools made
available via an SSE-based MCP Server.

## Table of contents

- Purpose
- Installation
- Configuration
- Output


## Purpose

The actual purpose of this module was to learn how to build an MCP Client.
The real-world use case that inspired it was a desire to make an LLM
that was trained in 2023 on data collected in 2022 (such as Clause Haiku 3.5)
but successfully answer complex questions about the 2025 MLB season.


## Installation

For now, this module runs as a CLI tool, and requires no installation
beyond:

```bash
   
   pip install -r requirements.txt
   ```

To run, you must have access to a running MCP server, and a configuration file,
described below.  There is a test operation (test) and a trade recommendation 
operation (trades):

```bash
   
   python -m mlbchat --operation test --config [[config.json]]
```

```bash
   
   python -m mlbchat --operation trades --config [[config.json]] --team "Washington Nationals"
```


## Configuration

The module will read your Anthropic credentials and the MCP server endpoint
you want to use from a JSON configuration file with very specific expectations
of keys and structure.  An example:

```json
   
   {
   "claude":
     {
     "api_key": "YOUR-API-KEY-HERE",
     "version": "2023-06-01",
     "model": "claude-3-5-haiku-20241022"
     },
   "baseballmcp":
     {
     "server": "http://127.0.0.1:8080"
     }
   }
```


## Output

The module is currently very verbose and writes results to standard output
in a non-machine readable format.

Three attempts to get trade recommendations are made:

- Simpleton: A very basic prompt with no context other than the team name

- Role-based: A system prompt describing the background and priorities of an MLB GM, followed by a detailed prompt for recommendations

- Tool-using: The role-based prompts along with all the tools described by the MCP Server.

The tool-using transcript is produced at each interactions, and then re-output
in its final state at the end of the char.  During the interaction, if the LLM
mentions 'Would you like me to' or 'look up specific players', a canned user
response is sent saying (essentially) 'Yes, please do.'

The tool-using chat will cut off after 10 messages have been sent (roughly, as
Haiku sometimes sends multi-part messages).  This can be changed in the following
line of baseball_client.py:

```python

   if queries_spent > 10:
```

### Current maintainers

- [Joshua Powers (jpowersbaseball)](https://github.com/jpowersbaseball/mlbchat)
