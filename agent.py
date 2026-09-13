"""Agent definition for the OKF Builder.

Loads configuration and the instruction prompt from YAML files, then wires
up a Google ADK agent backed by a local Ollama model with file-system and
web-search tools.
"""

import os

import google.adk.agents as agents
import google.adk.models.lite_llm as llm
import requests
import yaml
from bs4 import BeautifulSoup
from tavily import TavilyClient

MODEL = "ollama_chat/gemma4:12b"
TAVILY_API_KEY_ENV_VAR = "TAVILY_API_KEY"
FETCH_TIMEOUT_SECONDS = 10
MAX_PAGE_CHARS = 4000

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

with open("prompt.yaml", "r") as f:
    prompt = yaml.safe_load(f)

model = llm.LiteLlm(model=MODEL)
instruction = prompt["skills"] + "\nFollow user instructions."


def _resolve_path(path: str) -> str:
    """Join the configured root with a path relative to it."""
    return os.path.join(config["path-root"], path)


def write_file(path: str, name: str, content: str) -> str:
    """
    path: string representation of the location path - must be different from filename. Path must end in /
    name: string name of the file
    content: string content to write to the file
    """
    directory = _resolve_path(path)
    full_path = os.path.join(directory, name)
    try:
        os.makedirs(directory, exist_ok=True)
        with open(full_path, "w") as f:
            f.write(content)
        return f"Wrote: {full_path}"
    except OSError as e:
        return f"Error writing file: {full_path} ({e})"


def read_file(path: str, name: str) -> str:
    """
    path: string representation of the location path - must be different from filename. Path must end in /
    name: string name of the file
    """
    full_path = os.path.join(_resolve_path(path), name)
    if not os.path.exists(full_path):
        return f"File: {name} not found at path {path}"
    try:
        with open(full_path, "r") as f:
            return f.read()
    except OSError as e:
        return f"Error reading file: {full_path} ({e})"


def read_directory(path: str) -> str:
    """
    path: string representation of the location path - must be different from filename. Path must end in /
    """
    full_path = _resolve_path(path)
    if not os.path.exists(full_path):
        return f"Path not found: {full_path}"
    try:
        return "\n".join(os.listdir(full_path))
    except OSError as e:
        return f"Error reading path: {full_path} ({e})"


def remove_file(path: str, name: str) -> str:
    """
    path: string representation of the location path - must be different from filename. Path must end in /
    name: string name of the file
    """
    full_path = os.path.join(_resolve_path(path), name)
    if not os.path.exists(full_path):
        return f"File: {name} not found at path {path}"
    try:
        os.remove(full_path)
        return f"File removed: {full_path}"
    except OSError as e:
        return f"Error removing the file: {full_path} ({e})"


def _fetch_page_text(url: str) -> str:
    """Fetch a page and return its visible text, trimmed to MAX_PAGE_CHARS."""
    response = requests.get(url, timeout=FETCH_TIMEOUT_SECONDS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()

    text = " ".join(soup.get_text(separator=" ").split())
    return text[:MAX_PAGE_CHARS]


def search(query: str) -> str:
    """
    query: string to search for.
    """
    api_key = os.environ.get(TAVILY_API_KEY_ENV_VAR)
    if not api_key:
        return f"Error: {TAVILY_API_KEY_ENV_VAR} environment variable is not set"

    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(query=query, search_depth="advanced")
        results = response["results"]
    except Exception as e:
        return f"Error accessing websites: {e}"

    candidates = ""
    for r in results:
        if "edu" in r["url"] or "wikipedia" in r["url"]:
            try:
                content = _fetch_page_text(r["url"])
            except requests.RequestException:
                content = r["content"]  # fall back to Tavily's own snippet
            candidates += f'\nURL: {r["url"]}\nContent: {content}\n'

    return candidates if candidates else "No results"


root_agent = agents.Agent(
    name="OKF_Builder",
    description="Build OKF bundles",
    instruction=instruction,
    model=model,
    tools=[write_file, read_directory, read_file, remove_file, search],
)
