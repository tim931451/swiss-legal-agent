"""make_llm picks endpoint and key from the model id. Offline: building a client does not touch the network."""

from lexgraph.config import APERTUS_MODEL, CANDIDATE_MODELS, LLM_BASE_URL, SWISSAI_BASE_URL, make_llm


def test_routing(monkeypatch):
    monkeypatch.setenv("LITELLM_API_KEY", "proxy-key")
    monkeypatch.setenv("SWISSAI_API_KEY", "swissai-key")
    proxy = make_llm("azure_ai/gpt-oss-120b")
    swiss = make_llm(APERTUS_MODEL)
    assert proxy.openai_api_base == LLM_BASE_URL and proxy.openai_api_key.get_secret_value() == "proxy-key"
    assert swiss.openai_api_base == SWISSAI_BASE_URL and swiss.openai_api_key.get_secret_value() == "swissai-key"


def test_apertus_is_candidate():
    assert APERTUS_MODEL in CANDIDATE_MODELS and "v1.5" in APERTUS_MODEL
