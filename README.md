# okf_builder

A Google ADK agent (`root_agent` in [agent.py](agent.py)) backed by a local
Ollama model, with tools for reading/writing files and searching the web via
Tavily.

See [AGENTS.md](AGENTS.md) for conventions and context aimed at AI coding
agents working on this codebase.

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

## Running

With `config.yaml` and `prompt.yaml` present in the working directory, and
`TAVILY_API_KEY` set, run the agent through the ADK CLI/web UI, e.g.:

```bash
adk run okf_builder
# or
adk web
```

`agent.py` reads its configuration at import time, so `root_agent` is ready
as soon as the module loads.

## Tools

`root_agent` is given five tools, all defined in [agent.py](agent.py):

| Tool | Description |
| --- | --- |
| `write_file(path, name, content)` | Write text to a file under `path-root`, creating directories as needed. Overwrites existing files. |
| `read_file(path, name)` | Read and return a file's text content. |
| `read_directory(path)` | List the entries (files/subdirectories) at a path. |
| `remove_file(path, name)` | Delete a file. Not reversible. |
| `search(query)` | Search the web via Tavily, keep only `.edu`/Wikipedia results, and return their fetched page text. |

For all file tools, `path` is relative to `path-root` (from `config.yaml`)
and must end in `/`; it must not include the filename.

## Notes / known limitations

- `search`'s domain filter is a plain substring check on the URL (`"edu" in
  url or "wikipedia" in url`), so it can match unintended hosts (e.g. a
  domain containing "edu" outside the `.edu` TLD).
- Page text fetched by `search` is a naive HTML-to-text extraction (via
  BeautifulSoup) and may include navigation/boilerplate text alongside the
  article content; it is capped at `MAX_PAGE_CHARS` (4000) characters.
- The file tools operate only within `path-root` by convention, not by
  enforcement — they don't currently guard against a caller passing `../`
  segments to escape that root.
