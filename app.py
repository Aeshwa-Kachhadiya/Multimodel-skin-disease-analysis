import streamlit as st
from google import genai
import json
import os
import re
import base64
import uuid
import html
from typing import List, Dict, Optional
from datetime import datetime
from skin_disease_model import get_image_based_analysis

disease_keywords = {
    "akiec": [
        "scaly", "rough", "dry patch", "crust", "crusty", "sun damaged",
        "pink patch", "red patch", "sandpaper", "photo damage", "thin plate",
        "precancer", "precancerous"
    ],
    "bcc": [
        "pearly", "translucent", "shiny bump", "rolled edges", "rolled border",
        "bleeds", "bleeding", "sore that doesn't heal", "open sore",
        "small bump", "pink bump", "waxy", "ulcer", "rodent ulcer",
        "visible blood vessels", "telangiectasia"
    ],
    "bkl": [
        "stuck on", "warty", "wart like", "seborrheic", "brown spot", "flat brown",
        "age spot", "sun spot", "liver spot", "rough spot", "well defined",
        "light brown", "dark brown", "keratosis", "non cancerous growth"
    ],
    "df": [
        "firm bump", "hard bump", "dimple", "dimple sign",
        "small nodule", "brown nodule", "round bump",
        "insect bite like", "itchy nodule", "smooth dome",
        "fibrous bump"
    ],
    "mel": [
        "irregular", "asymmetry", "uneven border", "changing", "evolving",
        "multiple colors", "dark brown", "black patch", "bleeds", "enlarging",
        "growing quickly", "itchy mole", "new mole", "abnormal mole",
        "abcde", "color variation", "spreading", "large spot"
    ],
    "nv": [
        "mole", "brown mole", "flat mole", "raised mole", "uniform color",
        "symmetrical mole", "birthmark", "benign mole", "tan spot",
        "small brown spot", "regular borders", "smooth edges", 
        "harmless mole"
    ],
    "vasc": [
        "red spot", "purple spot", "blood spot", "cherry", "angioma",
        "bright red bump", "bleeds easily", "hemorrhage", "red papule",
        "angiokeratoma", "vascular lesion", "blue spot", "red nodule",
        "pyogenic granuloma"
    ]
}

disease_names = {
    "akiec": "Actinic Keratosis (Pre-cancerous)",
    "bcc": "Basal Cell Carcinoma",
    "bkl": "Benign Keratosis",
    "df": "Dermatofibroma",
    "mel": "Melanoma",
    "nv": "Melanocytic Nevus (Mole)",
    "vasc": "Vascular Lesion",
    "unknown": "Unknown - Please consult a dermatologist"
}

disease_treatments = {
    "akiec": {
        "severity": "High - Pre-cancerous",
        "treatments": [
            "Topical creams: Imiquimod, 5-fluorouracil (5-FU)",
            "Cryotherapy (freezing with liquid nitrogen)",
            "Photodynamic therapy (PDT)",
            "Chemical peels",
            "Surgical excision for advanced cases",
            "Sun protection and preventive measures"
        ],
        "urgent": True
    },
    "bcc": {
        "severity": "High - Skin Cancer",
        "treatments": [
            "Mohs micrographic surgery (most effective)",
            "Surgical excision",
            "Curettage and electrodesiccation",
            "Cryotherapy",
            "Radiation therapy",
            "Topical imiquimod or 5-FU for small lesions"
        ],
        "urgent": True
    },
    "bkl": {
        "severity": "Low - Benign",
        "treatments": [
            "Observation (no treatment needed if not bothersome)",
            "Cryotherapy (freezing)",
            "Surgical removal for cosmetic reasons",
            "Laser treatment",
            "Chemical peels",
            "Topical tretinoin may help"
        ],
        "urgent": False
    },
    "df": {
        "severity": "Low - Benign",
        "treatments": [
            "Observation (usually no treatment needed)",
            "Surgical excision for cosmetic concerns",
            "Cryotherapy",
            "Laser treatment",
            "Intralesional steroid injections"
        ],
        "urgent": False
    },
    "mel": {
        "severity": "Critical - Melanoma",
        "treatments": [
            "URGENT: Surgical excision with wide margins",
            "Sentinel lymph node biopsy",
            "Immunotherapy (pembrolizumab, nivolumab)",
            "Targeted therapy for BRAF mutations",
            "Chemotherapy if advanced",
            "Radiation therapy for metastatic disease"
        ],
        "urgent": True
    },
    "nv": {
        "severity": "Low - Benign",
        "treatments": [
            "Observation (no treatment needed)",
            "Surgical removal for cosmetic reasons",
            "Laser treatment",
            "Cryotherapy",
            "Dermabrasion"
        ],
        "urgent": False
    },
    "vasc": {
        "severity": "Low to Moderate",
        "treatments": [
            "Observation for small lesions",
            "Laser therapy (most effective)",
            "Cryotherapy",
            "Sclerotherapy (injection)",
            "Surgical removal",
            "Topical treatments"
        ],
        "urgent": False
    },
    "unknown": {
        "severity": "Unknown",
        "treatments": [
            "Consult a dermatologist for proper diagnosis",
            "Provide detailed description and photos",
            "Professional medical evaluation recommended"
        ],
        "urgent": False
    }
}

def match_disease_from_text(user_text: str) -> Dict:
    """Match skin condition based on symptom keywords in text."""
    text = user_text.lower()
    scores = {disease: 0 for disease in disease_keywords}
    matched_keywords = {disease: [] for disease in disease_keywords}

    for disease, keywords in disease_keywords.items():
        for keyword in keywords:
            if keyword in text:
                scores[disease] += 1
                matched_keywords[disease].append(keyword)

    if max(scores.values()) == 0:
        return {
            "condition": "unknown",
            "name": disease_names["unknown"],
            "score": 0,
            "matched_keywords": [],
            "all_scores": scores
        }

    best_match = max(scores, key=scores.get)
    return {
        "condition": best_match,
        "name": disease_names[best_match],
        "score": scores[best_match],
        "matched_keywords": matched_keywords[best_match],
        "all_scores": scores
    }

def init_session_state():
    if "conversations" not in st.session_state:
        st.session_state.conversations = {}
    if "current_conversation_id" not in st.session_state:
        new_id = create_new_conversation()
        st.session_state.current_conversation_id = new_id
    if "response_in_progress" not in st.session_state:
        st.session_state.response_in_progress = False
    if "editing_message_idx" not in st.session_state:
        st.session_state.editing_message_idx = None
    if "search_query" not in st.session_state:
        st.session_state.search_query = ""

def create_new_conversation() -> str:
    conv_id = str(uuid.uuid4())[:8]
    st.session_state.conversations[conv_id] = {
        "id": conv_id,
        "title": "New Chat",
        "created_at": datetime.now().isoformat(),
        "messages": [{"role": "system", "content": "You are a helpful assistant."}]
    }
    return conv_id

def get_current_messages() -> List[Dict]:
    conv_id = st.session_state.current_conversation_id
    if conv_id in st.session_state.conversations:
        return st.session_state.conversations[conv_id]["messages"]
    return [{"role": "system", "content": "You are a helpful assistant."}]

def set_current_messages(messages: List[Dict]):
    conv_id = st.session_state.current_conversation_id
    if conv_id in st.session_state.conversations:
        st.session_state.conversations[conv_id]["messages"] = messages

def update_conversation_title(conv_id: str, first_message: str):
    title = first_message[:40] + "..." if len(first_message) > 40 else first_message
    st.session_state.conversations[conv_id]["title"] = title

def format_code_blocks(text: str) -> str:
    """Convert markdown code blocks to syntax-highlighted HTML."""
    CODE_BLOCK_PLACEHOLDER = "\x00CODE_BLOCK_{}\x00"
    INLINE_CODE_PLACEHOLDER = "\x00INLINE_CODE_{}\x00"
    
    code_blocks = []
    inline_codes = []
    
    def store_code_block(match):
        lang = match.group(1) or "text"
        code = match.group(2)
        escaped_code = code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        html = f'<div class="code-block"><div class="code-header">{lang}</div><pre><code class="language-{lang}">{escaped_code}</code></pre></div>'
        idx = len(code_blocks)
        code_blocks.append(html)
        return CODE_BLOCK_PLACEHOLDER.format(idx)
    
    pattern = r'```(\w*)\n?([\s\S]*?)```'
    text = re.sub(pattern, store_code_block, text)
    
    def store_inline_code(match):
        code = match.group(1)
        escaped = code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        html = f'<code class="inline-code">{escaped}</code>'
        idx = len(inline_codes)
        inline_codes.append(html)
        return INLINE_CODE_PLACEHOLDER.format(idx)
    
    text = re.sub(r'`([^`]+)`', store_inline_code, text)
    
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    for idx, html in enumerate(code_blocks):
        text = text.replace(CODE_BLOCK_PLACEHOLDER.format(idx), html)
    for idx, html in enumerate(inline_codes):
        text = text.replace(INLINE_CODE_PLACEHOLDER.format(idx), html)
    
    return text

init_session_state()

st.set_page_config(page_title="Streamlit ChatGPT-like UI", layout="wide")
st.markdown(
    """
    <style>
    * { box-sizing: border-box; }
    .stApp { background: linear-gradient(135deg, #0a0f1f 0%, #0b1020 100%); color: #dbe7ff; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
    
    .chat-container {
        max-width: 100%;
        padding: 24px;
        display: flex;
        flex-direction: column;
        gap: 14px;
    }
    
    .message-wrapper {
        display: flex;
        margin: 8px 0;
        width: 100%;
    }
    
    .message-wrapper.user {
        justify-content: flex-end;
    }
    
    .message-wrapper.assistant {
        justify-content: flex-start;
    }
    
    .bubble {
        padding: 12px 16px;
        border-radius: 14px;
        line-height: 1.6;
        font-size: 14px;
        width: fit-content;
        max-width: 70%;
        min-width: 60px;
        word-wrap: break-word;
        overflow-wrap: break-word;
        white-space: pre-wrap;
    }
    
    .bubble.user {
        background: #000000;
        color: #ffffff;
        border-bottom-right-radius: 2px;
        box-shadow: 0 3px 12px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.15);
    }
    
    .bubble.assistant {
        background: #1a2332;
        color: #e6eef8;
        border-bottom-left-radius: 2px;
        border: 1.5px solid rgba(108, 158, 248, 0.3);
        box-shadow: 0 3px 12px rgba(0, 0, 0, 0.15);
    }
    
    .code-block {
        background: #0f1620;
        border-radius: 8px;
        margin: 12px 0;
        overflow: hidden;
        border: 1px solid rgba(108, 158, 248, 0.1);
    }
    
    .code-header {
        background: #1a2332;
        padding: 8px 12px;
        font-size: 11px;
        color: #6c9ef8;
        border-bottom: 1px solid rgba(108, 158, 248, 0.2);
        font-weight: 600;
        text-transform: uppercase;
    }
    
    .code-block pre {
        margin: 0;
        padding: 12px;
        overflow-x: auto;
        font-size: 12px;
    }
    
    .code-block code {
        font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, monospace;
        color: #e6eef8;
        white-space: pre;
    }
    
    .inline-code {
        background: #1a2332;
        padding: 3px 8px;
        border-radius: 4px;
        font-family: 'SF Mono', Monaco, monospace;
        font-size: 13px;
        color: #f8b86c;
        border: 1px solid rgba(108, 158, 248, 0.1);
    }
    
    .conversation-item {
        padding: 10px 12px;
        margin: 4px 0;
        border-radius: 8px;
        cursor: pointer;
        background: #1a2332;
        border: 1px solid rgba(108, 158, 248, 0.1);
        font-size: 13px;
    }
    
    .conversation-item:hover {
        background: #232d3d;
        border-color: rgba(108, 158, 248, 0.3);
    }
    
    .conversation-item.active {
        background: #2d3d52;
        border-color: #6c9ef8;
        box-shadow: 0 0 12px rgba(108, 158, 248, 0.2);
    }
    
    .image-preview {
        max-width: 300px;
        max-height: 300px;
        border-radius: 12px;
        margin: 10px 0;
        border: 1px solid rgba(108, 158, 248, 0.2);
    }
    
    [data-testid="stForm"] {
        border-top: 1px solid rgba(108, 158, 248, 0.1);
        padding-top: 20px;
        margin-top: 20px;
    }
    
    .stButton button {
        border-radius: 6px;
        font-weight: 500;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.title("Chat Controls")
    
    st.markdown("### Conversations")
    search_query = st.text_input("Search conversations", value=st.session_state.search_query, placeholder="Search...", key="search_input")
    st.session_state.search_query = search_query
    
    if st.button("New Chat", use_container_width=True):
        new_id = create_new_conversation()
        st.session_state.current_conversation_id = new_id
        st.rerun()
    
    sorted_convs = sorted(
        st.session_state.conversations.items(),
        key=lambda x: x[1].get("created_at", ""),
        reverse=True
    )
    
    for conv_id, conv in sorted_convs:
        title = conv.get("title", "New Chat")
        if search_query:
            messages_text = " ".join([m.get("content", "") for m in conv.get("messages", [])])
            if search_query.lower() not in title.lower() and search_query.lower() not in messages_text.lower():
                continue
        
        is_active = conv_id == st.session_state.current_conversation_id
        btn_type = "primary" if is_active else "secondary"
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(title[:30], key=f"conv_{conv_id}", use_container_width=True, type=btn_type):
                st.session_state.current_conversation_id = conv_id
                st.session_state.editing_message_idx = None
                st.rerun()
        with col2:
            if st.button("X", key=f"del_{conv_id}"):
                if len(st.session_state.conversations) > 1:
                    del st.session_state.conversations[conv_id]
                    if st.session_state.current_conversation_id == conv_id:
                        st.session_state.current_conversation_id = list(st.session_state.conversations.keys())[0]
                    st.rerun()
    
    st.markdown("---")
    st.markdown("### Settings")
    
    api_key = st.text_input(
        "Google AI API Key", 
        type="password", 
        placeholder="AIzaSy...", 
        help="Get it from https://aistudio.google.com/apikey",
        value=os.environ.get("GEMINI_API_KEY", "")
    )
    # The newest Gemini model is gemini-2.5-pro or gemini-2.5-flash
    # do not change this unless explicitly requested by the user
    model = st.selectbox("Model", options=["gemini-2.5-pro", "gemini-2.5-flash", "gemini-1.5-pro", "gemini-1.5-flash"], index=0)
    temperature = st.slider("Temperature", 0.0, 2.0, 1.0)
    max_tokens = st.slider("Max tokens (response)", 256, 8192, 2048)
    
    current_messages = get_current_messages()
    system_content = current_messages[0]["content"] if current_messages else "You are a helpful assistant."
    system_prompt = st.text_area("System prompt", value=system_content, height=80)
    
    if st.button("Reset current conversation"):
        set_current_messages([{"role": "system", "content": system_prompt or "You are a helpful assistant."}])
        st.session_state.conversations[st.session_state.current_conversation_id]["title"] = "New Chat"
        st.rerun()

    st.markdown("---")
    st.write("Export / Import")
    st.download_button(
        "Download conversation JSON", 
        data=json.dumps(get_current_messages(), indent=2), 
        file_name="conversation.json", 
        mime="application/json"
    )
    uploaded = st.file_uploader("Upload conversation JSON", type=["json"])
    if uploaded is not None:
        try:
            new_msgs = json.load(uploaded)
            if isinstance(new_msgs, list):
                set_current_messages(new_msgs)
                st.success("Conversation loaded.")
                st.rerun()
            else:
                st.error("Uploaded file must be a JSON list of messages.")
        except Exception as e:
            st.error(f"Failed to load: {e}")

current_messages = get_current_messages()
if current_messages:
    current_messages[0]["content"] = system_prompt or current_messages[0]["content"]
    set_current_messages(current_messages)

left_col, right_col = st.columns([3, 1])

with left_col:
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

    messages_holder = st.container()
    with messages_holder:
        current_messages = get_current_messages()
        for idx, msg in enumerate(current_messages):
            role = msg.get("role", "assistant")
            content = msg.get("content", "")
            if role == "system":
                continue
            
            cls = "assistant" if role == "assistant" else "user"
            author = "Assistant" if role == "assistant" else "You"
            
            if st.session_state.editing_message_idx == idx:
                new_content = st.text_area(
                    f"Edit message ({author})", 
                    value=content, 
                    key=f"edit_{idx}",
                    height=100
                )
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("Save", key=f"save_{idx}"):
                        current_messages[idx]["content"] = new_content
                        set_current_messages(current_messages)
                        st.session_state.editing_message_idx = None
                        st.rerun()
                with col2:
                    if st.button("Cancel", key=f"cancel_{idx}"):
                        st.session_state.editing_message_idx = None
                        st.rerun()
                with col3:
                    if role == "user" and st.button("Save & Regenerate", key=f"regen_{idx}"):
                        current_messages[idx]["content"] = new_content
                        messages_after = current_messages[:idx+1]
                        set_current_messages(messages_after)
                        st.session_state.editing_message_idx = None
                        st.rerun()
            else:
                if "image_data" in msg:
                    img_mime = msg.get("image_mime", "image/png")
                    st.markdown(f'<img src="data:{img_mime};base64,{msg["image_data"]}" class="image-preview"/>', unsafe_allow_html=True)
                
                # Format content (handles code blocks and escaping)
                clean_content = content.strip()
                if clean_content.endswith("</div>"):
                    clean_content = clean_content[:-6].strip()
                formatted_content = format_code_blocks(clean_content)
                
                # Create chat bubble with proper alignment
                if role == "assistant":
                    st.markdown(f'<div style="text-align: left; margin: 10px 0; clear: both;"><div style="background: #0f1724; color: #e6eef8; padding: 12px 16px; border-radius: 18px; border-bottom-left-radius: 4px; border: 1px solid rgba(255,255,255,0.04); word-wrap: break-word; overflow-wrap: break-word; white-space: pre-wrap; line-height: 1.5;">{formatted_content}</div></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div style="text-align: right; margin: 10px 0; clear: both;"><div style="background: #6c9ef8; color: #02214d; padding: 12px 16px; border-radius: 18px; border-bottom-right-radius: 4px; word-wrap: break-word; overflow-wrap: break-word; white-space: pre-wrap; line-height: 1.5;">{formatted_content}</div></div>', unsafe_allow_html=True)
                
                # Display skin analysis if available for this user message
                if role == "user" and "analysis" in msg:
                    analysis = msg["analysis"]
                    condition = analysis.get("condition", "unknown")
                    if condition != "unknown":
                        treatment_info = disease_treatments.get(condition, {})
                        condition_colors = {
                            "mel": "#ff4b4b",
                            "bcc": "#ffa500",
                            "akiec": "#ffa500",
                            "bkl": "#4CAF50",
                            "df": "#4CAF50",
                            "nv": "#4CAF50",
                            "vasc": "#2196F3"
                        }
                        color = condition_colors.get(condition, "#888")
                        
                        st.markdown(f"""
                        <div style="background: {color}22; border-left: 4px solid {color}; padding: 10px; border-radius: 4px; margin: 10px 0;">
                            <strong style="color: {color};">🔍 Analysis: {analysis["name"]}</strong><br>
                            <small>Severity: {treatment_info.get("severity", "Unknown")}</small>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if analysis.get("matched_keywords"):
                            st.markdown("**Symptoms found:**")
                            st.write(", ".join(analysis["matched_keywords"]))
                        
                        st.markdown("**Treatment Options:**")
                        for i, treatment in enumerate(treatment_info.get("treatments", []), 1):
                            st.write(f"{i}. {treatment}")
                        
                        if treatment_info.get("urgent"):
                            st.error("⚠️ URGENT: Consult a dermatologist immediately!")
                
                action_cols = st.columns([1, 1, 1, 3])
                with action_cols[0]:
                    if st.button("Edit", key=f"edit_btn_{idx}", help="Edit this message"):
                        st.session_state.editing_message_idx = idx
                        st.rerun()
                with action_cols[1]:
                    if role == "assistant" and st.button("Regen", key=f"regen_btn_{idx}", help="Regenerate response"):
                        messages_before = current_messages[:idx]
                        set_current_messages(messages_before)
                        st.rerun()
                with action_cols[2]:
                    if st.button("Delete", key=f"del_btn_{idx}", help="Delete this message"):
                        del current_messages[idx]
                        set_current_messages(current_messages)
                        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

with right_col:
    st.markdown("### Conversation")
    user_msg_count = len([m for m in get_current_messages() if m['role'] != 'system'])
    st.write(f"Messages: {user_msg_count}")
    st.markdown("---")
    st.markdown("Quick prompts")
    if st.button("Explain my code"):
        msgs = get_current_messages()
        msgs.append({"role": "user", "content": "Please explain the following code I will paste next."})
        set_current_messages(msgs)
        if user_msg_count == 0:
            update_conversation_title(st.session_state.current_conversation_id, "Explain my code")
        st.rerun()
    if st.button("Summarize last message"):
        msgs = get_current_messages()
        msgs.append({"role": "user", "content": "Summarize your last message in one short paragraph."})
        set_current_messages(msgs)
        st.rerun()
    if st.button("Write Python code"):
        msgs = get_current_messages()
        msgs.append({"role": "user", "content": "Write Python code for the following task:"})
        set_current_messages(msgs)
        if user_msg_count == 0:
            update_conversation_title(st.session_state.current_conversation_id, "Write Python code")
        st.rerun()
    
    st.markdown("---")
    st.markdown("### Skin Condition Analyzer")
    skin_description = st.text_area(
        "Describe your skin symptoms",
        placeholder="e.g., I have a rough, scaly patch that's pink...",
        height=100,
        key="skin_input"
    )
    if st.button("Analyze Symptoms", use_container_width=True):
        if skin_description.strip():
            result = match_disease_from_text(skin_description)
            st.session_state.skin_analysis_result = result
        else:
            st.warning("Please describe your symptoms first.")
    
    if "skin_analysis_result" in st.session_state and st.session_state.skin_analysis_result:
        result = st.session_state.skin_analysis_result
        condition = result["condition"]
        
        if condition == "unknown":
            st.info("No specific condition identified. Please describe symptoms in more detail or consult a dermatologist.")
        else:
            treatment_info = disease_treatments.get(condition, {})
            
            condition_colors = {
                "mel": "#ff4b4b",
                "bcc": "#ffa500",
                "akiec": "#ffa500",
                "bkl": "#4CAF50",
                "df": "#4CAF50",
                "nv": "#4CAF50",
                "vasc": "#2196F3"
            }
            color = condition_colors.get(condition, "#888")
            
            st.markdown(f"""
            <div style="background: {color}22; border-left: 4px solid {color}; padding: 10px; border-radius: 4px; margin: 10px 0;">
                <strong style="color: {color};">{result["name"]}</strong><br>
                <small>Severity: {treatment_info.get("severity", "Unknown")}</small>
            </div>
            """, unsafe_allow_html=True)
            
            if result["matched_keywords"]:
                st.markdown("**Symptoms found:**")
                st.write(", ".join(result["matched_keywords"]))
            
            st.markdown("**Treatment Options:**")
            for i, treatment in enumerate(treatment_info.get("treatments", []), 1):
                st.write(f"{i}. {treatment}")
            
            if treatment_info.get("urgent"):
                st.error("⚠️ URGENT: Consult a dermatologist immediately for professional evaluation.")
            else:
                st.info("Consult a dermatologist for professional diagnosis and treatment recommendation.")
        
        if st.button("Clear"):
            if "skin_analysis_result" in st.session_state:
                del st.session_state.skin_analysis_result
            st.rerun()

st.markdown("### Send a Message")

uploaded_image = st.file_uploader("Upload an image for analysis (optional)", type=["png", "jpg", "jpeg", "gif", "webp"], key="image_upload")

with st.form(key="input_form", clear_on_submit=True):
    user_input = st.text_area("Message", placeholder="Type your message and press Send", height=120)
    cols = st.columns([1, 1])
    send = cols[0].form_submit_button("Send")
    clear = cols[1].form_submit_button("Clear input")

if clear:
    st.rerun()

def get_gemini_client(api_key: str):
    return genai.Client(api_key=api_key)

def gemini_stream_chat(client, messages: List[Dict], model: str, temperature: float, max_tokens: int):
    try:
        from google.genai import types
        system_text = None
        api_messages = []
        
        for m in messages:
            if m["role"] == "system":
                system_text = m["content"]
                continue
            
            role = "user" if m["role"] == "user" else "model"
            parts = []
            
            if "image_data" in m and m["role"] == "user":
                img_mime = m.get("image_mime", "image/png")
                parts.append(types.Part(text=m["content"]))
                parts.append(types.Part(inline_data=types.Blob(mime_type=img_mime, data=base64.b64decode(m["image_data"]))))
            else:
                parts.append(types.Part(text=m["content"]))
            
            api_messages.append(types.Content(role=role, parts=parts))
        
        config_dict = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        if system_text:
            config_dict["system_instruction"] = system_text
        
        response = client.models.generate_content_stream(
            model=model,
            contents=api_messages,
            config=types.GenerateContentConfig(**config_dict),
        )
        
        for chunk in response:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        yield f"\n\n[Error while streaming response: {e}]"

def gemini_chat_complete(client, messages: List[Dict], model: str, temperature: float, max_tokens: int) -> str:
    try:
        from google.genai import types
        system_text = None
        api_messages = []
        
        for m in messages:
            if m["role"] == "system":
                system_text = m["content"]
                continue
            
            role = "user" if m["role"] == "user" else "model"
            parts = []
            
            if "image_data" in m and m["role"] == "user":
                img_mime = m.get("image_mime", "image/png")
                parts.append(types.Part(text=m["content"]))
                parts.append(types.Part(inline_data=types.Blob(mime_type=img_mime, data=base64.b64decode(m["image_data"]))))
            else:
                parts.append(types.Part(text=m["content"]))
            
            api_messages.append(types.Content(role=role, parts=parts))
        
        config_dict = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        if system_text:
            config_dict["system_instruction"] = system_text
        
        response = client.models.generate_content(
            model=model,
            contents=api_messages,
            config=types.GenerateContentConfig(**config_dict)
        )
        return response.text if response.text else "[No response generated]"
    except Exception as e:
        return f"[Error generating response: {e}]"

if send and user_input:
    msgs = get_current_messages()
    new_msg = {"role": "user", "content": user_input}
    
    if uploaded_image is not None:
        image_bytes = uploaded_image.read()
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        mime_type = uploaded_image.type or "image/png"
        new_msg["image_data"] = image_b64
        new_msg["image_mime"] = mime_type
        
        try:
            condition, confidence, name = get_image_based_analysis(image_bytes)
            if condition != "unknown":
                analysis = {
                    "condition": condition,
                    "name": name,
                    "score": confidence,
                    "matched_keywords": [],
                    "all_scores": {}
                }
                new_msg["analysis"] = analysis
        except Exception as e:
            pass
    
    # Auto-analyze for skin conditions from text
    text_analysis = match_disease_from_text(user_input)
    if "analysis" not in new_msg and text_analysis["condition"] != "unknown":
        new_msg["analysis"] = text_analysis
    
    msgs.append(new_msg)
    set_current_messages(msgs)
    
    user_msgs = [m for m in msgs if m["role"] == "user"]
    if len(user_msgs) == 1:
        update_conversation_title(st.session_state.current_conversation_id, user_input)
    
    st.rerun()

def last_non_system_role():
    msgs = get_current_messages()
    for m in reversed(msgs):
        if m["role"] in ("user", "assistant"):
            return m["role"]
    return None

if last_non_system_role() == "user":
    if api_key:
        st.session_state.response_in_progress = True
        msgs = get_current_messages()
        assistant_msg = {"role": "assistant", "content": ""}
        msgs.append(assistant_msg)
        set_current_messages(msgs)

        placeholder = st.empty()
        text_so_far = ""
        
        client = get_gemini_client(api_key)
        messages_to_send = [m for m in get_current_messages()[:-1]]

        try:
            for chunk in gemini_stream_chat(client, messages_to_send, model, temperature, max_tokens):
                text_so_far += chunk
                msgs = get_current_messages()
                msgs[-1]["content"] = text_so_far.strip()
                set_current_messages(msgs)
        except Exception as stream_error:
            try:
                full = gemini_chat_complete(client, messages_to_send, model, temperature, max_tokens)
                full_trimmed = full.strip()
                msgs = get_current_messages()
                msgs[-1]["content"] = full_trimmed
                set_current_messages(msgs)
            except Exception as e:
                msgs = get_current_messages()
                msgs[-1]["content"] = f"Error: {str(e)[:100]}"
                set_current_messages(msgs)
        finally:
            st.session_state.response_in_progress = False
            st.rerun()
    else:
        st.warning("No Google AI API key provided. Get one free at https://aistudio.google.com/apikey")

st.markdown(
    """
    <div style="opacity:0.7; margin-top:12px; font-size:13px;">
    Built with Streamlit — Chat UI inspired by ChatGPT.
    </div>
    """,
    unsafe_allow_html=True,
)
