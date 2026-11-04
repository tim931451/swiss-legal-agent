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
SWISSAI_PREFIXES = ("CSCS-Inference/", "RCP-AIaaS/", "SwissAI-Research/")  # model ids served by the Swiss AI Platform
# T08 (13.10.2026): Apertus-70B-Instruct-2509 rejects the tools parameter (error 400 from its chat template),
# Apertus-v1.5-70B and v1.5-8B return correct tool_calls. See docs/decisions.md.
APERTUS_MODEL = "CSCS-Inference/swiss-ai/Apertus-v1.5-70B"

# Embeddings (notebook 02). The FHNW proxy serves two embedding models, both compared in T12 (docs/eval/retrieval).
SWISS_EMBED_MODEL = "andreasmartin/apertus-v1.1-swiss-embed-0.4b"  # Swiss embedding model (notebook 02)
HARRIER_EMBED_MODEL = "leoipulsar/harrier-0.6b:latest"  # Ollama build of Microsoft harrier-oss-v1-0.6b
EMBED_MODEL = HARRIER_EMBED_MODEL  # used by retrieve(); T12: Hit@1 0.9 against 0.4 for the Swiss model (10 cases)
# T12: the proxy offers no reranker model, so a chat model reranks the first-stage hits (lexgraph/rag/retrieval.py).
RERANK_MODEL = LLM_MODEL

# Evaluation (notebook 06)
CANDIDATE_MODELS = ["azure_ai/gpt-oss-120b", "gpt-5.6-luna", APERTUS_MODEL]
JUDGE_MODEL = "azure_ai/mistral-large-3"  # different model family than the candidates, to limit self-preference


def make_llm(model=LLM_MODEL, base_url=None, key_env=None, temperature=0):
    """Create a chat model. Only model, endpoint and key change between providers.

    Without base_url the endpoint follows the model id: Swiss AI Platform ids go to SWISSAI_BASE_URL with
    SWISSAI_API_KEY, everything else to the FHNW proxy with LITELLM_API_KEY.
    """
    on_swissai = model.startswith(SWISSAI_PREFIXES)
    base_url = base_url or (SWISSAI_BASE_URL if on_swissai else LLM_BASE_URL)
    key_env = key_env or ("SWISSAI_API_KEY" if on_swissai else "LITELLM_API_KEY")
    return ChatOpenAI(model=model, base_url=base_url, api_key=os.environ[key_env], temperature=temperature)
