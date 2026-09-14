# AGENTS.md

Guidance for AI coding agents working in this repository. Human-facing docs
are in [README.md](README.md).

## What this is

A single-file Google ADK agent. `agent.py` builds `root_agent`, an
`LlmAgent` that runs on a local Ollama model (via `litellm`) and exposes
five Python functions as tools. There is no framework/CLI code here beyond
that — the ADK runtime (`adk run` / `adk web`) imports `agent.py` and calls
`root_agent` itself.

## Repo layout

- `agent.py` — the entire implementation: config/prompt loading, the five
  tools, and the `root_agent` definition.
- `README.md` — setup and usage for humans.
- No test suite, no build step, no linter config currently exist in this
  repo.

Two files it depends on at runtime live **outside this repo**, in the
current working directory when the agent is run: `config.yaml` (needs a
`path-root` key) and `prompt.yaml` (needs a `skills` key). Don't assume
they're present when reasoning about this repo in isolation — see
[README.md](README.md#configuration) for their shape.

## Conventions to follow when editing agent.py

- **Tool docstrings are runtime behavior, not just comments.** ADK passes
  each tool function's docstring to the LLM as its description. Every tool
  docstring should have a one-line summary of what it does, an `Args:`
  section, and a `Returns:` section describing what the string return value
  means (these functions return human-readable status/error strings, not
  exceptions, so callers — including the LLM — rely on the docstring to
  know what a given return string means).
- **Tools return strings, they don't raise.** Every tool catches its own
  errors (`OSError` for file ops, `Exception`/`requests.RequestException`
  for network calls) and returns a descriptive string instead of letting
  exceptions propagate, since the caller is an LLM tool-call loop, not code
  that can catch exceptions. Keep new tools consistent with this pattern —
  no bare `except:`; catch the narrowest applicable exception type and
  return a message that includes the underlying error.
- **Path handling goes through `_resolve_path`.** All file tools resolve
  `path` against `config["path-root"]` via `_resolve_path`, then join the
  filename with `os.path.join`. Don't string-concatenate paths directly —
  that reintroduced separator bugs once already (see git history).
- **No secrets in source.** `search`'s Tavily API key must keep coming from
  the `TAVILY_API_KEY` environment variable (`TAVILY_API_KEY_ENV_VAR`), not
  a literal string — a hardcoded key was previously committed here and had
  to be removed/rotated.
- **Network calls need a timeout.** `_fetch_page_text` uses
  `FETCH_TIMEOUT_SECONDS`; any new outbound request should set an explicit
  timeout rather than blocking indefinitely.

## Verifying a change

There's no test suite. At minimum:

```bash
python -m py_compile agent.py
```

To actually exercise the module (requires `config.yaml`/`prompt.yaml` in
the cwd, and network access for `search`):

```python
import importlib.util
spec = importlib.util.spec_from_file_location("agent", "agent.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print(mod.root_agent.name)       # confirms root_agent built
print(mod.search("test query"))  # exercises Tavily + page fetch + fallback
```

## Git

Commits in this repo should carry `Co-Authored-By` attribution per whatever
the invoking session's attribution convention is at the time — check the
most recent commit messages for the current format rather than assuming.
