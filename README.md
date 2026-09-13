# okf_builder

A Google ADK agent (`root_agent` in [agent.py](agent.py)) backed by a local
Ollama model, with tools for reading/writing files and searching the web via
Tavily.

## Requirements

- Python with `google-adk`, `litellm`, `pyyaml`, `requests`, `beautifulsoup4`,
  `tavily-python` installed.
- A local Ollama server running the model referenced by `MODEL` in
  [agent.py](agent.py) (default: `gemma4:12b`).
- Environment variable `TAVILY_API_KEY` set to a valid Tavily API key (used
  by the `search` tool).

## Configuration

This module expects two YAML files in the **current working directory** when
it's run (they are not part of this repo):

- `config.yaml` — must define `path-root`, the root directory the file
  tools (`read_file`, `write_file`, `read_directory`, `remove_file`) operate
  relative to.
- `prompt.yaml` — must define a `skills` key holding the instruction text
  prepended to the agent's system instruction.
