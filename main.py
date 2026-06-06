
import streamlit as st
import google.generativeai as genai
from datetime import datetime
import uuid
import json
import os
import base64
import pytz

st.set_page_config(page_title="Bharat AI", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

# --- API KEY ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

CHAT_FILE = "chats.json"

# --- INDIAN TIME ---
def get_india_time():
    ist = pytz.timezone("Asia/Kolkata")
    return datetime.now(ist)

def load_chats():
    if os.path.exists(CHAT_FILE):
        try:
            with open(CHAT_FILE, "r", encoding="utf-8") as f:
                chats = json.load(f)
            for chat in chats.values():
                chat["created_at"] = datetime.fromisoformat(chat["created_at"])
            return chats
        except:
            return {}
    return {}

def save_chats():
    chats_to_save = {}
    for chat_id, chat_data in st.session_state.chats.items():
        chats_to_save[chat_id] = {
            "title": chat_data["title"],
            "messages": [
                {k: v for k, v in msg.items() if k != "image_data"} 
                for msg in chat_data["messages"]
            ],
            "created_at": chat_data["created_at"].isoformat()
        }
    with open(CHAT_FILE, "w", encoding="utf-8") as f:
        json.dump(chats_to_save, f, ensure_ascii=False, indent=2)

SYSTEM_PROMPT = f"You are Bharat AI. Reply in user's language. Hindi→Hindi, Hinglish→Hinglish, English→English. Be direct and helpful. Current date and time in India: {get_india_time().strftime('%d %B %Y, %I:%M %p IST')}"
model = genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=SYSTEM_PROMPT)

# --- CSS ---
st.markdown("""
<style>
.stApp { background-color: #000000; }
[data-testid="stSidebar"] {
    background-color: #0A0A0A!important;
    border-right: 1px solid #262626;
    min-width: 320px!important;
    max-width: 320px!important;
}
[data-testid="collapsedControl"] {display: none!important;}
#MainMenu, footer {visibility: hidden;}
.stButton > button {
    width: 100%;
    background: linear-gradient(90deg, #4F46E5 0%, #7C3AED 100%);
    color: white!important;
    border: none;
    border-radius: 10px;
    padding: 0.6rem;
    font-weight: 600;
}
.stMarkdown,.stMarkdown p {color: #FFFFFF!important;}
h1 {color: #FFFFFF!important;}
.stChatInput textarea {
    background-color: #1A1A1A!important;
    color: #FFFFFF!important;
    border: 1px solid #262626!important;
    border-radius: 24px!important;
}
.export-btn > button {
    background: linear-gradient(90deg, #059669 0%, #047857 100%)!important;
}
.stDownloadButton > button {
    width: 100%;
    background: linear-gradient(90deg, #059669 0%, #047857 100%);
    color: white!important;
    border: none;
    border-radius: 10px;
    padding: 0.6rem;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if "chats" not in st.session_state:
    st.session_state.chats = load_chats()

if "current_chat_id" not in st.session_state:
    if st.session_state.chats:
        st.session_state.current_chat_id = sorted(
            st.session_state.chats.items(),
            key=lambda x: x[1]["created_at"], reverse=True
        )[0][0]
    else:
        new_id = str(uuid.uuid4())
        st.session_state.current_chat_id = new_id
        st.session_state.chats[new_id] = {
            "title": "New Chat",
            "messages": [],
            "created_at": get_india_time()
        }
        save_chats()

if "chat_session" not in st.session_state:
    history = []
    for msg in st.session_state.chats[st.session_state.current_chat_id]["messages"]:
        role = "user" if msg["role"] == "user" else "model"
        history.append({"role": role, "parts": [msg["content"]]})
    st.session_state.chat_session = model.start_chat(history=history)

if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

# --- FUNCTIONS ---
def new_chat():
    new_id = str(uuid.uuid4())
    st.session_state.current_chat_id = new_id
    st.session_state.chats[new_id] = {
        "title": "New Chat",
        "messages": [],
        "created_at": get_india_time()
    }
    st.session_state.chat_session = model.start_chat(history=[])
    st.session_state.uploaded_image = None
    save_chats()
    st.rerun()

def switch_chat(chat_id):
    st.session_state.current_chat_id = chat_id
    history = []
    for msg in st.session_state.chats[chat_id]["messages"]:
        role = "user" if msg["role"] == "user" else "model"
        history.append({"role": role, "parts": [msg["content"]]})
    st.session_state.chat_session = model.start_chat(history=history)
    st.session_state.uploaded_image = None
    st.rerun()

def delete_chat(chat_id):
    del st.session_state.chats[chat_id]
    if st.session_state.current_chat_id == chat_id:
        if st.session_state.chats:
            st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]
        else:
            new_chat()
            return
    save_chats()
    st.rerun()

def export_chat_txt(chat_data):
    """Chat ko plain text mein export karo"""
    lines = []
    lines.append(f"=== {chat_data['title']} ===")
    lines.append(f"Export Date: {get_india_time().strftime('%d %B %Y, %I:%M %p IST')}")
    lines.append("=" * 40)
    lines.append("")
    for msg in chat_data["messages"]:
        role = "Aap" if msg["role"] == "user" else "Bharat AI"
        timestamp = msg.get("timestamp", "")
        if timestamp:
            lines.append(f"[{timestamp}] {role}:")
        else:
            lines.append(f"{role}:")
        lines.append(msg["content"])
        lines.append("")
    return "\n".join(lines)

def export_chat_json(chat_data):
    """Chat ko JSON mein export karo"""
    export_data = {
        "title": chat_data["title"],
        "exported_at": get_india_time().strftime("%d %B %Y, %I:%M %p IST"),
        "messages": [
            {
                "role": msg["role"],
                "content": msg["content"],
                "timestamp": msg.get("timestamp", "")
            }
            for msg in chat_data["messages"]
        ]
    }
    return json.dumps(export_data, ensure_ascii=False, indent=2)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("## ⚡ Bharat AI")
    
    # Indian time show karo
    ist_time = get_india_time()
    st.markdown(
        f"<p style='color: #A3A3A3; font-size: 0.75rem; margin: 0 0 1rem 0;'>🕐 {ist_time.strftime('%d %b %Y, %I:%M %p')} IST</p>",
        unsafe_allow_html=True
    )
    
    if st.button("➕ New Chat", use_container_width=True, key="new"):
        new_chat()

    # --- IMAGE UPLOAD ---
    st.markdown("<p style='color: #A3A3A3; font-size: 0.8rem; font-weight: 600; margin: 1rem 0 0.5rem 0;'>📷 IMAGE UPLOAD</p>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "JPG/PNG upload karo",
        type=["jpg", "jpeg", "png"],
        key="img_uploader",
        label_visibility="collapsed"
    )
    if uploaded_file is not None:
        st.session_state.uploaded_image = uploaded_file
        st.image(uploaded_file, caption="Image ready ✅", use_column_width=True)
        if st.button("❌ Image Hatao", key="clear_img"):
            st.session_state.uploaded_image = None
            st.rerun()

    st.markdown("<p style='color: #A3A3A3; font-size: 0.8rem; font-weight: 600; margin: 1rem 0 0.5rem 0;'>RECENT CHATS</p>", unsafe_allow_html=True)
    
    sorted_chats = sorted(st.session_state.chats.items(), key=lambda x: x[1]["created_at"], reverse=True)
    for chat_id, chat_data in sorted_chats:
        title = chat_data.get("title", "New Chat")[:25]
        col1, col2 = st.columns([5, 1])
        with col1:
            if chat_id == st.session_state.current_chat_id:
                st.button(f"💬 {title}", key=f"c_{chat_id}", type="primary", use_container_width=True, disabled=True)
            else:
                if st.button(f"💬 {title}", key=f"c_{chat_id}", use_container_width=True):
                    switch_chat(chat_id)
        with col2:
            if st.button("🗑️", key=f"d_{chat_id}"):
                delete_chat(chat_id)

# --- MAIN AREA ---
current_chat = st.session_state.chats[st.session_state.current_chat_id]

if len(current_chat["messages"]) == 0:
    st.markdown("<div style='text-align: center; margin-top: 20vh;'>", unsafe_allow_html=True)
    st.title("⚡ Bharat AI")
    st.caption("Namaste! Main Bharat AI hoon. Kya puchna hai?")
    st.markdown("</div>", unsafe_allow_html=True)
else:
    # --- EXPORT BUTTONS (messages hone par dikhao) ---
    col_exp1, col_exp2, col_spacer = st.columns([1, 1, 4])
    with col_exp1:
        txt_content = export_chat_txt(current_chat)
        st.download_button(
            label="📄 Export TXT",
            data=txt_content,
            file_name=f"{current_chat['title'][:20]}_chat.txt",
            mime="text/plain",
            key="export_txt"
        )
    with col_exp2:
        json_content = export_chat_json(current_chat)
        st.download_button(
            label="📦 Export JSON",
            data=json_content,
            file_name=f"{current_chat['title'][:20]}_chat.json",
            mime="application/json",
            key="export_json"
        )
    st.markdown("<div style='padding-top: 1rem;'></div>", unsafe_allow_html=True)

# --- SHOW MESSAGES ---
for msg in current_chat["messages"]:
    timestamp = msg.get("timestamp", "")
    ts_html = f"<div style='color: #666; font-size: 11px; margin-top: 4px;'>{timestamp}</div>" if timestamp else ""
    
    if msg["role"] == "user":
        img_html = ""
        if msg.get("has_image"):
            img_html = "<div style='color: #A3A3A3; font-size: 12px; margin-bottom: 4px;'>📷 Image attached</div>"
        st.markdown(f"""
        <div style='display: flex; justify-content: flex-end; margin-bottom: 16px;'>
            <div style='background-color: #1A1A1A; padding: 12px 16px; border-radius: 18px; max-width: 70%; border: 1px solid #262626;'>
                {img_html}
                <div style='color: #FFFFFF; line-height: 1.6; font-size: 15px;'>{msg["content"]}</div>
                {ts_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style='display: flex; gap: 12px; margin-bottom: 24px; align-items: flex-start;'>
            <div style='width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); flex-shrink: 0; margin-top: 2px;'></div>
            <div style='max-width: 85%; padding-top: 4px;'>
                <div style='color: #FFFFFF; line-height: 1.7; font-size: 15px;'>{msg["content"]}</div>
                {ts_html}
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- CHAT INPUT ---
if prompt := st.chat_input("Message likho... (image upload sidebar se karo)"):
    if current_chat["title"] == "New Chat" and len(current_chat["messages"]) == 0:
        current_chat["title"] = prompt[:30] + "..." if len(prompt) > 30 else prompt

    now_str = get_india_time().strftime("%I:%M %p")
    has_image = st.session_state.uploaded_image is not None

    # User message store karo
    current_chat["messages"].append({
        "role": "user",
        "content": prompt,
        "timestamp": now_str,
        "has_image": has_image
    })

    # User message dikhao
    img_html = "<div style='color: #A3A3A3; font-size: 12px; margin-bottom: 4px;'>📷 Image attached</div>" if has_image else ""
    st.markdown(f"""
    <div style='display: flex; justify-content: flex-end; margin-bottom: 16px;'>
        <div style='background-color: #1A1A1A; padding: 12px 16px; border-radius: 18px; max-width: 70%; border: 1px solid #262626;'>
            {img_html}
            <div style='color: #FFFFFF; line-height: 1.6; font-size: 15px;'>{prompt}</div>
            <div style='color: #666; font-size: 11px; margin-top: 4px;'>{now_str}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # AI response
    try:
        with st.spinner(""):
            if has_image:
                # Image ke saath message bhejo
                img_file = st.session_state.uploaded_image
                img_bytes = img_file.getvalue()
                mime_type = "image/jpeg" if img_file.name.lower().endswith((".jpg", ".jpeg")) else "image/png"
                
                image_part = {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": base64.b64encode(img_bytes).decode("utf-8")
                    }
                }
                response = st.session_state.chat_session.send_message([image_part, prompt])
                st.session_state.uploaded_image = None  # Image use hone ke baad clear karo
            else:
                response = st.session_state.chat_session.send_message(prompt)
            
            ai_reply = response.text

        ai_time = get_india_time().strftime("%I:%M %p")
        st.markdown(f"""
        <div style='display: flex; gap: 12px; margin-bottom: 24px; align-items: flex-start;'>
            <div style='width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); flex-shrink: 0; margin-top: 2px;'></div>
            <div style='max-width: 85%; padding-top: 4px;'>
                <div style='color: #FFFFFF; line-height: 1.7; font-size: 15px;'>{ai_reply}</div>
                <div style='color: #666; font-size: 11px; margin-top: 4px;'>{ai_time}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        current_chat["messages"].append({
            "role": "assistant",
            "content": ai_reply,
            "timestamp": ai_time
        })
        save_chats()
        st.rerun()

    except Exception as e:
        st.error(f"Error: {e}")