"""Model endpoints, model names and the one chat-model factory used everywhere.

Source: notebook 01 (building block to take away), model names from notebooks 01, 02 and 06.
Importing this module never needs a key and never touches the network. `make_llm` reads the key only when called.
"""

import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# load_dotenv never overwrites variables that are already set (Deepnote integration first, then .env).
load_dotenv()

# FHNW LiteLLM proxy (OpenAI-compatible)
LLM_BASE_URL = "https://litellm.engines.aisl.science/v1"
LLM_MODEL = "azure_ai/gpt-oss-120b"  # default model for development
COMMERCIAL_MODEL = "gpt-5.6-luna"  # commercial reference model for experiment F1

# Swiss AI Platform (CSCS), hosts Apertus
SWISSAI_BASE_URL = "https://api.swissai.svc.cscs.ch/v1"
# TODO (T08): set the Apertus model name found with list_models() in notebook 01, section 5.
APERTUS_MODEL = None

# Embeddings (notebook 02)
EMBED_MODEL = "andreasmartin/apertus-v1.1-swiss-embed-0.4b"  # Swiss embedding model on the FHNW proxy

# Evaluation (notebook 06)
CANDIDATE_MODELS = ["azure_ai/gpt-oss-120b", "gpt-5.6-luna"]  # add Apertus once notebook 01 found its name
JUDGE_MODEL = "azure_ai/mistral-large-3"  # different model family than the candidates, to limit self-preference


def make_llm(model="azure_ai/gpt-oss-120b", base_url=LLM_BASE_URL, key_env="LITELLM_API_KEY", temperature=0):
    """Create a chat model. Only model, endpoint and key change between providers."""
    return ChatOpenAI(model=model, base_url=base_url, api_key=os.environ[key_env], temperature=temperature)
