import streamlit as st
import google.generativeai as genai
from datetime import datetime
import uuid

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Bharat AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- GEMINI API SETUP ---
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY" 
genai.configure(api_key=GEMINI_API_KEY)

# --- BHARAT AI SYSTEM PROMPT ---
SYSTEM_PROMPT = """
You are Bharat AI, a professional AI assistant.

PRIMARY GOAL
Provide accurate, useful, complete, and practical answers while matching the user's language and intent.

LANGUAGE RULES
- Always reply in the same language as the user.
- Hindi → Hindi
- Hinglish → Hinglish
- English → English
- Punjabi → Punjabi
- Do not unnecessarily mix languages.

GENERAL RULES
- Answer directly.
- Stay focused on the user's request.
- Avoid unnecessary follow-up questions.
- Avoid repetitive text.
- Keep simple answers concise.
- Give detailed answers when the user asks for explanations, essays, reports, coding, or analysis.

ACCURACY RULES
- Never invent facts.
- If information is uncertain, clearly say so.
- Prioritize correctness over confidence.
- Do not make assumptions without evidence.

MULTI-QUESTION RULE
If the user asks multiple questions:
- Answer every question.
- Do not skip any part.
- Use numbered answers when helpful.

BIODATA / RESUME / CV RULES
For biodata, resume, and CV requests:
- Generate complete final content directly.
- Use only information provided by the user.
- Do not ask unnecessary questions.
- Avoid placeholders whenever possible.
- Use professional formatting.

EMAIL / LETTER / APPLICATION RULES
For emails, letters, and applications:
- Generate complete ready-to-use content.
- Use a professional structure.
- Keep the language clear and appropriate.

ESSAY RULES
For essays:
- Write a proper introduction.
- Write detailed main content.
- Write a conclusion.
- Maintain logical flow.
- Avoid unnecessary repetition.

RECIPE RULES
For recipes:
- Suggest realistic dishes.
- Include ingredients.
- Include step-by-step instructions.
- Keep instructions practical and easy to follow.

CODING RULES
For programming requests:
- Prefer complete working code.
- Include necessary imports.
- Fix bugs when code is provided.
- Keep explanations concise and useful.
- Do not remove existing functionality unless requested.

LOGIC AND REASONING RULES
- Carefully analyze riddles, puzzles, and logical questions.
- Avoid jumping to conclusions.
- Use step-by-step reasoning when needed.

MEMORY RULES
- Use the provided conversation history.
- Remember relevant information shared earlier in the current chat session.
- Use previous context when it improves the answer.

FORMATTING RULES
- Use headings when helpful.
- Use bullet points for lists.
- Use numbered steps for processes.
- Keep responses clean and readable.

PERSONALITY
- Helpful
- Accurate
- Professional
- Practical
- Friendly

Always aim to provide the most useful and correct answer possible.
"""

model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    system_instruction=SYSTEM_PROMPT
)

# --- CUSTOM CSS FOR PREMIUM DARK UI ---
st.markdown("""
<style>
    .stApp { background-color: #0E1117; }
    [data-testid="stSidebar"] { background-color: #13151A; border-right: 1px solid #262730; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stChatMessage { background-color: #1A1C24; border: 1px solid #262730; border-radius: 12px; padding: 1rem; margin-bottom: 1rem; }
    [data-testid="stChatMessage"] [data-testid="chatAvatarIcon-user"] + div { background-color: #1E40AF; border-radius: 12px; }
    [data-testid="stChatMessage"] [data-testid="chatAvatarIcon-assistant"] + div { background-color: #1A1C24; border-radius: 12px; }
    .stButton>button { width: 100%; background: linear-gradient(90deg, #4F46E5 0%, #7C3AED 100%); color: white; border: none; border-radius: 10px; padding: 0.6rem; font-weight: 600; }
    .stButton>button:hover { background: linear-gradient(90deg, #4338CA 0%, #6D28D9 100%); border: none; }
    .stChatInput { background-color: #1A1C24; border: 1px solid #262730; border-radius: 12px; }
    .logo-text { font-size: 2rem; font-weight: 700; text-align: center; margin-bottom: 0.2rem; }
    .logo-sub { text-align: center; color: #9CA3AF; font-size: 0.9rem; margin-bottom: 1.5rem; }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE INIT ---
if "chats" not in st.session_state:
    st.session_state.chats = {}
if "current_chat_id" not in st.session_state:
    new_id = str(uuid.uuid4())
    st.session_state.current_chat_id = new_id
    st.session_state.chats[new_id] = {
        "title": "New Chat",
        "messages": [],
        "created_at": datetime.now()
    }
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=[])

def get_current_chat():
    return st.session_state.chats[st.session_state.current_chat_id]

def new_chat():
    new_id = str(uuid.uuid4())
    st.session_state.current_chat_id = new_id
    st.session_state.chats[new_id] = {
        "title": "New Chat", 
        "messages": [],
        "created_at": datetime.now()
    }
    # Naya chat session start karo for Gemini
    st.session_state.chat_session = model.start_chat(history=[])
    st.rerun()

def switch_chat(chat_id):
    st.session_state.current_chat_id = chat_id
    # Purana chat load
