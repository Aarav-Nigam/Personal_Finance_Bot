import streamlit as st

from config.settings import settings
from llm.advisor import get_advice_stream_with_tools
from ui.styles import inject_css, section_header
from ui.theme import COLORS

inject_css()

section_header("AI Portfolio Advisor", icon="🤖")

with st.sidebar:
    provider = st.selectbox(
        "LLM Provider",
        ["gemini", "groq", "ollama"],
        index=["gemini", "groq", "ollama"].index(st.session_state.get("llm_provider", "gemini")),
    )
    st.session_state.llm_provider = provider

    if provider == "gemini" and settings.GOOGLE_API_KEY:
        st.markdown(
            f'<span style="color:{COLORS["profit"]}">&#9679;</span> Gemini connected',
            unsafe_allow_html=True,
        )
    elif provider == "groq" and settings.GROQ_API_KEY:
        st.markdown(
            f'<span style="color:{COLORS["profit"]}">&#9679;</span> Groq connected',
            unsafe_allow_html=True,
        )
    elif provider == "ollama":
        url = settings.OLLAMA_BASE_URL
        st.markdown(
            f'<span style="color:{COLORS["primary"]}">&#9679;</span> Ollama: {url}',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<span style="color:{COLORS["loss"]}">&#9679;</span> No API key for {provider}',
            unsafe_allow_html=True,
        )

if "messages" not in st.session_state:
    st.session_state.messages = []

QUICK_QUERIES = [
    ("Portfolio Review", "Give me an overview of my portfolio performance"),
    ("Top Holdings", "What are my top holdings and how are they doing?"),
    ("Sector Exposure", "Analyse my sector exposure and suggest rebalancing"),
    ("Stock Signal", "What's the buy/sell signal for RELIANCE?"),
    ("Market Pulse", "What's the current market status?"),
    ("Latest News", "What's the latest news on my top holdings?"),
]

cols = st.columns(3)
for i, (label, query) in enumerate(QUICK_QUERIES):
    if cols[i % 3].button(label, key=f"quick_{i}", use_container_width=True):
        st.session_state.quick_query = query

if st.button("Clear conversation", type="secondary"):
    st.session_state.messages = []
    st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("tool_calls"):
            with st.expander("🔍 Data fetched", expanded=False):
                for tc in msg["tool_calls"]:
                    st.caption(f"✓ {tc['display']}")
        st.write(msg["content"])

prompt = st.chat_input("Ask about your portfolio, stocks, or market...")

if hasattr(st.session_state, "quick_query"):
    prompt = st.session_state.quick_query
    del st.session_state.quick_query

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    holdings_df = st.session_state.get("holdings_df")
    llm_history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]

    with st.chat_message("assistant"):
        tool_container = st.container()
        text_container = st.empty()
        tool_calls_ui = []
        full_text = ""

        try:
            for event in get_advice_stream_with_tools(prompt, holdings_df, llm_history):
                if event["type"] == "tool_call":
                    tool_calls_ui.append(event)
                    with tool_container:
                        st.caption(f"🔍 {event['display']}")

                elif event["type"] == "text_delta":
                    full_text += event["content"]
                    text_container.markdown(full_text + "▌")

                elif event["type"] == "done":
                    text_container.markdown(event["full_text"])
                    full_text = event["full_text"]

        except Exception as e:
            full_text = f"Error: {e}"
            text_container.error(full_text)

        st.session_state.messages.append({
            "role": "assistant",
            "content": full_text,
            "tool_calls": [{"name": tc["name"], "display": tc["display"]} for tc in tool_calls_ui],
        })
