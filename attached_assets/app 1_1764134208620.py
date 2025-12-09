# app.py
import streamlit as st
import openai
import json
from typing import List, Dict
import time

# ---------------------------
# Helper: initialize session
# ---------------------------
if "messages" not in st.session_state:
    # messages is a list of dicts: {"role": "user"|"assistant"|"system", "content": "..."}
    st.session_state.messages: List[Dict] = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]
if "response_in_progress" not in st.session_state:
    st.session_state.response_in_progress = False

# ---------------------------
# Page layout & sidebar
# ---------------------------
st.set_page_config(page_title="Streamlit ChatGPT-like UI", layout="wide")
st.markdown(
    """
    <style>
    /* page background */
    .stApp { background: #0b1020; color: #dbe7ff; }

    /* main chat container */
    .chat-container{
        max-width: 900px;
        margin: 18px auto;
        padding: 18px;
    }

    /* chat bubbles */
    .bubble {
        display: inline-block;
        padding: 12px 16px;
        border-radius: 18px;
        margin: 6px 0;
        max-width: 80%;
        line-height: 1.45;
        font-size: 15px;
        white-space: pre-wrap;
    }
    .user {
        background: #6c9ef8;
        color: #02214d;
        border-bottom-right-radius: 4px;
        float: right;
        clear: both;
    }
    .assistant {
        background: #0f1724;
        color: #e6eef8;
        border-bottom-left-radius: 4px;
        float: left;
        clear: both;
        border: 1px solid rgba(255,255,255,0.04);
    }

    .meta {
        font-size: 12px;
        opacity: 0.7;
        margin-bottom: 6px;
    }

    /* message area container */
    .messages { padding-bottom: 120px; }

    /* clear floats */
    .clearfix::after { content: ""; clear: both; display: table; }

    /* bottom input fixed area */
    .input-area {
        position: sticky;
        bottom: 12px;
        background: transparent;
        padding-top: 8px;
    }

    /* minimal scroll behavior */
    .messages::-webkit-scrollbar { width: 8px; }
    .messages::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.08); border-radius: 8px; }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.title("Chat Controls")
    api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...", help="You can also set OPENAI_API_KEY env var.")
    model = st.selectbox("Model", options=["gpt-4o", "gpt-4", "gpt-3.5-turbo"], index=2)
    temperature = st.slider("Temperature", 0.0, 1.0, 0.2, 0.05)
    max_tokens = st.slider("Max tokens (response)", 64, 2000, 512, 64)
    system_prompt = st.text_area("System prompt (optional)", value=st.session_state.messages[0]["content"], height=80)
    if st.button("Reset conversation"):
        st.session_state.messages = [{"role": "system", "content": system_prompt or "You are a helpful assistant."}]
        st.experimental_rerun()

    st.markdown("---")
    st.write("Export / Import")
    if st.button("Download conversation JSON"):
        st.download_button("Download JSON", data=json.dumps(st.session_state.messages, indent=2), file_name="conversation.json", mime="application/json")
    uploaded = st.file_uploader("Upload conversation JSON", type=["json"])
    if uploaded is not None:
        try:
            new_msgs = json.load(uploaded)
            if isinstance(new_msgs, list):
                st.session_state.messages = new_msgs
                st.success("Conversation loaded.")
                st.experimental_rerun()
            else:
                st.error("Uploaded file must be a JSON list of messages.")
        except Exception as e:
            st.error(f"Failed to load: {e}")

# apply system prompt change (but keep original list structure)
st.session_state.messages[0]["content"] = system_prompt or st.session_state.messages[0]["content"]

# ---------------------------
# Main area: conversation
# ---------------------------
left_col, right_col = st.columns([3, 1])

with left_col:
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

    messages_holder = st.container()
    with messages_holder:
        # Render messages
        for msg in st.session_state.messages:
            role = msg.get("role", "assistant")
            content = msg.get("content", "")
            if role == "system":
                continue  # hide system in chat
            cls = "assistant" if role == "assistant" else "user"
            author = "Assistant" if role == "assistant" else "You"
            st.markdown(
                f"""
                <div class="clearfix">
                  <div class="meta">{author}</div>
                  <div class="bubble {cls}">{st.markdown.__wrapped__.__name__ and content}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)

with right_col:
    st.markdown("### Conversation")
    st.write(f"Messages: {len([m for m in st.session_state.messages if m['role'] != 'system'])}")
    st.markdown("---")
    st.markdown("Quick prompts")
    if st.button("Explain my code"):
        st.session_state.messages.append({"role": "user", "content": "Please explain the following code I will paste next."})
        st.experimental_rerun()
    if st.button("Summarize last assistant message"):
        st.session_state.messages.append({"role": "user", "content": "Summarize your last message in one short paragraph."})
        st.experimental_rerun()

# ---------------------------
# Input form at bottom
# ---------------------------
with st.form(key="input_form", clear_on_submit=False):
    user_input = st.text_area("Message", placeholder="Type your message and press Send", height=120)
    cols = st.columns([1, 1, 1])
    send = cols[0].form_submit_button("Send")
    clear = cols[1].form_submit_button("Clear input")
    stop_button = cols[2].form_submit_button("Stop stream (if running)")

if clear:
    st.experimental_rerun()

# ---------------------------
# OpenAI helpers (streaming)
# ---------------------------
def openai_stream_chat(messages, api_key, model, temperature, max_tokens):
    """
    Generator that yields chunks of assistant text as they arrive.
    Uses openai.ChatCompletion.create(..., stream=True) style.
    """
    openai.api_key = api_key
    try:
        # Use the classic streaming ChatCompletion endpoint.
        # Note: different openai versions / SDKs may vary. This is compatible with openai-python v0.x style.
        resp = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        partial = ""
        for chunk in resp:
            # chunk is a dict; we append delta content if present
            try:
                delta = chunk["choices"][0]["delta"]
                content = delta.get("content", "")
                if content:
                    partial += content
                    yield content
                # handle finish reason (non-zero)
                if chunk["choices"][0].get("finish_reason"):
                    break
            except Exception:
                # yield nothing if structure unexpected
                continue
        return
    except Exception as e:
        # if streaming failed, yield an error message
        yield f"\n\n[Error while streaming response: {e}]"

def openai_chat_complete(messages, api_key, model, temperature, max_tokens):
    openai.api_key = api_key
    resp = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=False,
    )
    return resp["choices"][0]["message"]["content"]

# ---------------------------
# Sending messages & streaming UI update
# ---------------------------
if send and user_input:
    # append user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    # rerun to show the user message immediately
    st.experimental_rerun()

# If last message is user and there is no assistant reply yet, call API
# Find last non-system message
def last_non_system_role():
    for m in reversed(st.session_state.messages):
        if m["role"] in ("user", "assistant"):
            return m["role"]
    return None

# if last role is user and there is no assistant after it, generate
if last_non_system_role() == "user":
    # check if assistant reply already present after the last user; we assume not
    # start streaming response
    if api_key:
        st.session_state.response_in_progress = True
        assistant_msg = {"role": "assistant", "content": ""}
        st.session_state.messages.append(assistant_msg)

        # Place a placeholder in the UI to append streaming text
        placeholder = st.empty()
        text_so_far = ""

        # Try streaming; if that fails, fallback to full completion
        try:
            for chunk in openai_stream_chat(st.session_state.messages, api_key, model, temperature, max_tokens):
                text_so_far += chunk
                # re-render conversation with updated assistant message
                st.session_state.messages[-1]["content"] = text_so_far
                # Render conversation area again (simple approach: rerun)
                placeholder.markdown(f"<div class='bubble assistant'>{text_so_far}</div>", unsafe_allow_html=True)
                time.sleep(0.01)  # small sleep so UI updates fluidly
        except Exception:
            # fallback to non-streaming
            try:
                full = openai_chat_complete(st.session_state.messages[:-1], api_key, model, temperature, max_tokens)
                st.session_state.messages[-1]["content"] = full
                placeholder.markdown(f"<div class='bubble assistant'>{full}</div>", unsafe_allow_html=True)
            except Exception as e:
                st.session_state.messages[-1]["content"] = f"[Error generating response: {e}]"
                placeholder.markdown(f"<div class='bubble assistant'>[Error generating response: {e}]</div>", unsafe_allow_html=True)
        finally:
            st.session_state.response_in_progress = False
            # Rerun so the full conversation renders in main area
            st.experimental_rerun()
    else:
        st.warning("No OpenAI API key provided. Enter your key in the sidebar to get responses.")

# ---------------------------
# Footer / credits
# ---------------------------
st.markdown(
    """
    <div style="opacity:0.7; margin-top:12px; font-size:13px;">
    Built with Streamlit — Chat UI inspired by ChatGPT.
    </div>
    """,
    unsafe_allow_html=True,
)
