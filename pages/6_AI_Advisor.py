import streamlit as st

from config.settings import settings
from llm.advisor import get_advice_stream
from ui.styles import inject_css, section_header
from ui.theme import COLORS

inject_css()

section_header("AI Portfolio Advisor", icon="robot_face")

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
    ("Rebalance Portfolio", "Suggest portfolio rebalancing"),
    ("Sell Recommendations", "Which stocks should I sell?"),
    ("Sector Exposure", "Analyse my sector exposure"),
    ("SIP Fund Picks", "Recommend SIP funds for 5 years"),
    ("XIRR vs Benchmark", "Explain my XIRR vs benchmark"),
    ("Tax Situation", "What is my tax situation?"),
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
        st.write(msg["content"])

prompt = st.chat_input("Ask about your portfolio...")

if hasattr(st.session_state, "quick_query"):
    prompt = st.session_state.quick_query
    del st.session_state.quick_query

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    holdings_df = st.session_state.get("holdings_df")
    history = st.session_state.messages[:-1]

    with st.chat_message("assistant"):
        try:
            response = st.write_stream(get_advice_stream(prompt, holdings_df, history))
            st.session_state.messages.append({"role": "assistant", "content": response})
        except Exception as e:
            error_msg = f"Error: {e}"
            st.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
