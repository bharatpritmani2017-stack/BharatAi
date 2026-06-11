import streamlit as st
import google.generativeai as genai
from datetime import datetime
import uuid, json, os, base64, pytz, io, textwrap, re
import html as html_lib

st.set_page_config(page_title="Bharat AI", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

from dotenv import load_dotenv
load_dotenv()
genai.configure(api_key=os.environ.get("AQ.Ab8RN6LPv_XMqXFb4DcrAaW2EpREHztJZkViFcJuglb8JEj-Og", ""))

CHAT_FILE = "chats.json"

def get_india_time():
    return datetime.now(pytz.timezone("Asia/Kolkata"))

def load_chats():
    if os.path.exists(CHAT_FILE):
        try:
            with open(CHAT_FILE, "r", encoding="utf-8") as f:
                chats = json.load(f)
            for chat in chats.values():
                chat["created_at"] = datetime.fromisoformat(chat["created_at"])
            return chats
        except: return {}
    return {}

def save_chats():
    chats_to_save = {}
    for cid, cd in st.session_state.chats.items():
        chats_to_save[cid] = {
            "title": cd["title"],
            "messages": [{k:v for k,v in m.items() if k != "image_data"} for m in cd["messages"]],
            "created_at": cd["created_at"].isoformat()
        }
    with open(CHAT_FILE, "w", encoding="utf-8") as f:
        json.dump(chats_to_save, f, ensure_ascii=False, indent=2)

def needs_export(text):
    t = text.lower().strip()
    return any(k in t for k in ["pdf bana","pdf bnao","pdf banao","pdf de","pdf chahiye","pdf bna","pdf dedo","txt bana","txt bnao","txt de","text file"])

def create_pdf(text, title="Bharat AI"):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas as rc
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.colors import HexColor
    for p in ["C:/Windows/Fonts/NotoSansDevanagari-Regular.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        if os.path.exists(p):
            fp = p; break
    else: fp = None
    buf = io.BytesIO()
    c = rc.Canvas(buf, pagesize=A4)
    w, h = A4
    fn = 'Helvetica'
    try:
        if fp: pdfmetrics.registerFont(TTFont('HF', fp)); fn = 'HF'
    except: pass
    c.setFont(fn,16); c.setFillColor(HexColor('#4F46E5'))
    c.drawCentredString(w/2, h-55, title[:60])
    c.setFont(fn,9); c.setFillColor(HexColor('#787878'))
    c.drawCentredString(w/2, h-75, f"Bharat AI | {get_india_time().strftime('%d %B %Y, %I:%M %p IST')}")
    c.setStrokeColor(HexColor('#4F46E5')); c.line(40,h-85,w-40,h-85)
    c.setFillColor(HexColor('#1E1E1E')); c.setFont(fn,11); y=h-110
    for line in text.split('\n'):
        if not line.strip(): y-=8
        else:
            cl = line.replace('**','').replace('*','').replace('#','').strip()
            for wl in textwrap.wrap(cl,85):
                if y<50: c.showPage(); c.setFont(fn,11); c.setFillColor(HexColor('#1E1E1E')); y=h-50
                c.drawString(40,y,wl); y-=18
    c.save(); return buf.getvalue()

def dl_link(data, filename, label, mime):
    b64 = base64.b64encode(data).decode()
    return f'<a href="data:{mime};base64,{b64}" download="{filename}" style="display:inline-flex;align-items:center;gap:6px;background:linear-gradient(135deg,#4F46E5,#7C3AED);color:#FFF;text-decoration:none;padding:10px 20px;border-radius:10px;font-size:13px;font-weight:600;margin:4px 2px;">{label}</a>'

def fmt_msg(content):
    def rep_code(m):
        lang = m.group(1) or "code"
        code = html_lib.escape(m.group(2).strip())
        cid = abs(hash(code[:20])) % 99999
        return f"<div class='cb'><div class='ch'><span class='cl'>{lang}</span><button class='cpb' onclick='var el=document.getElementById(\"c{cid}\");var t=document.createElement(\"textarea\");t.value=el.innerText;document.body.appendChild(t);t.select();document.execCommand(\"copy\");document.body.removeChild(t);this.innerHTML=\"✅\";setTimeout(()=>this.innerHTML=\"📋 Copy\",1500)'>📋 Copy</button></div><pre><code id='c{cid}'>{code}</code></pre></div>"
    content = re.sub(r'```(\w*)\n?([\s\S]*?)```', rep_code, content)
    content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
    return content.replace('\n','<br>')

def get_model():
    return genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=f"""Tu Bharat AI hai — India ka smart AI assistant. Banaya hai Bharat Pritmani ne, Jaipur, Rajasthan se.
Naam pooche → "Main Bharat AI hoon! 😊"
Kisne banaya → "Bharat Pritmani ne, Jaipur se!"
Style: Dost jaisa, seedha jawab, Hindi/English jo likhe.
EXPORT pe sirf bol: "✅ Neeche download button aa gaya!"
Time: {get_india_time().strftime('%d %B %Y, %I:%M %p IST')}"""
    )

# ── SESSION STATE ──────────────────────────────────────────────────────────────
if "chats" not in st.session_state: st.session_state.chats = load_chats()
if "cid" not in st.session_state: st.session_state.cid = None
if "uploaded_image" not in st.session_state: st.session_state.uploaded_image = None
if "dark_mode" not in st.session_state: st.session_state.dark_mode = True
if "msg_count" not in st.session_state:
    st.session_state.msg_count = 0
    st.session_state.msg_date = get_india_time().strftime("%Y-%m-%d")

today = get_india_time().strftime("%Y-%m-%d")
if st.session_state.msg_date != today:
    st.session_state.msg_count = 0
    st.session_state.msg_date = today

dm = st.session_state.dark_mode

# ── SIDEBAR (3-dot panel replacement — 100% working) ──────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style='text-align:center;padding:16px 0 8px;'>
        <div style='width:48px;height:48px;background:linear-gradient(135deg,#4338CA,#7C3AED);
            border-radius:14px;display:inline-flex;align-items:center;justify-content:center;font-size:24px;'>⚡</div>
        <div style='font-size:16px;font-weight:700;margin-top:8px;'>Bharat AI ✨</div>
        <div style='font-size:11px;color:#888;'>Aapka AI Saathi</div>
    </div>""", unsafe_allow_html=True)

    st.divider()

    # New Chat
    if st.button("＋ New Chat", use_container_width=True, type="primary"):
        nid = str(uuid.uuid4())
        st.session_state.chats[nid] = {"title":"New Chat","messages":[],"created_at":get_india_time()}
        st.session_state.cid = nid
        st.session_state.uploaded_image = None
        save_chats(); st.rerun()

    # Dark/Light mode
    mode_lbl = "☀️ Light Mode" if dm else "🌙 Dark Mode"
    if st.button(mode_lbl, use_container_width=True):
        st.session_state.dark_mode = not st.session_state.dark_mode; st.rerun()

    st.divider()

    # Current chat controls
    if st.session_state.cid and st.session_state.cid in st.session_state.chats:
        st.caption("CURRENT CHAT")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear", use_container_width=True):
                st.session_state.chats[st.session_state.cid]["messages"] = []
                st.session_state.chats[st.session_state.cid]["title"] = "New Chat"
                save_chats(); st.rerun()
        with col2:
            if st.button("🔴 Delete", use_container_width=True):
                del st.session_state.chats[st.session_state.cid]
                st.session_state.cid = None
                save_chats(); st.rerun()

        # Export
        cc_exp = st.session_state.chats.get(st.session_state.cid, {})
        if cc_exp.get("messages"):
            st.divider()
            st.caption("EXPORT CHAT")
            et = f"Bharat AI Chat\n{get_india_time().strftime('%d %B %Y, %I:%M %p IST')}\n{'='*40}\n\n"
            for m in cc_exp["messages"]:
                et += f"[{'You' if m['role']=='user' else 'Bharat AI'}] {m.get('timestamp','')}\n{m['content']}\n\n"
            ds = get_india_time().strftime('%d%m%Y')
            st.download_button("📝 TXT Download", data=et.encode(), file_name=f"chat_{ds}.txt", mime="text/plain", use_container_width=True)
            try:
                pdf = create_pdf(et, cc_exp.get("title","Bharat AI"))
                st.download_button("📄 PDF Download", data=pdf, file_name=f"chat_{ds}.pdf", mime="application/pdf", use_container_width=True)
            except: pass

    st.divider()

    # Stats
    st.caption(f"💬 Aaj ke messages: {st.session_state.msg_count}/1500")

    st.divider()

    # Recent chats
    st.caption("RECENT CHATS")
    search = st.text_input("🔍", placeholder="Search...", label_visibility="collapsed")
    for cid, cd in sorted(st.session_state.chats.items(), key=lambda x: x[1]["created_at"], reverse=True):
        t = cd.get("title","New Chat")[:25]
        if search.lower() in t.lower():
            is_active = cid == st.session_state.cid
            btn_type = "primary" if is_active else "secondary"
            if st.button(f"💬 {t}", key=f"chat_{cid}", use_container_width=True, type=btn_type):
                st.session_state.cid = cid; st.rerun()

    st.divider()
    st.markdown("""<div style='text-align:center;font-size:11px;color:#555;line-height:1.8;'>
        🤖 Bharat AI<br>by Bharat Pritmani<br>Jaipur 🇮🇳</div>""", unsafe_allow_html=True)

# ── COLORS ────────────────────────────────────────────────────────────────────
BG    = "#0F0F0F" if dm else "#F0F2F5"
MSGBG = "#1A1A1A" if dm else "#FFFFFF"
MSGBD = "#2A2A2A" if dm else "#E5E7EB"
MSGC  = "#E5E5E5" if dm else "#111111"
HDRBG = "#0F0F0F" if dm else "#FFFFFF"
INBG  = "#1A1A1A" if dm else "#FFFFFF"
INC   = "#FFFFFF" if dm else "#111111"
BOTBG = "#0F0F0F" if dm else "#F0F2F5"
TC    = "#FFFFFF" if dm else "#111111"
SC    = "#888888" if dm else "#555555"

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
*{{font-family:'Inter',sans-serif;box-sizing:border-box;}}
.stApp{{background:{BG}!important;}}
#MainMenu,footer{{visibility:hidden;}}
header{{visibility:hidden;}}
.stDeployButton{{display:none!important;}}

    border:1px solid {'#333' if dm else '#E5E7EB'};
    border-radius:50%;
    align-items:center;justify-content:center;
}}
::-webkit-scrollbar{{width:3px;}}
[data-testid="collapsedControl"]{{display:none!important;}}
/* Custom Panel */
.panel-overlay{{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.6);z-index:998;display:none;}}
.panel-overlay.open{{display:block;}}
.side-panel{{position:fixed;top:0;right:0;width:82vw;max-width:310px;height:100vh;background:{'#141414' if dm else '#fff'};z-index:999;transform:translateX(100%);transition:transform 0.28s ease;overflow-y:auto;box-shadow:-4px 0 20px rgba(0,0,0,0.4);}}
.side-panel.open{{transform:translateX(0);}}


}}

/* Style real Streamlit sidebar toggle as 3-dot button */




::-webkit-scrollbar-thumb{{background:#333;border-radius:4px;}}
.hdr{{display:flex;align-items:center;padding:10px 14px;
    border-bottom:1px solid {'#1E1E1E' if dm else '#E5E7EB'};
    background:{HDRBG};position:sticky;top:0;z-index:200;}}
.h-av{{width:38px;height:38px;background:linear-gradient(135deg,#4338CA,#7C3AED);
    border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:18px;margin-right:10px;}}
.h-name{{font-size:16px;font-weight:700;color:{TC};}}
.h-dot{{display:flex;align-items:center;gap:5px;font-size:11px;color:#22C55E;margin-top:2px;}}
.h-dot::before{{content:'';width:6px;height:6px;background:#22C55E;border-radius:50%;display:inline-block;}}
.h-menu{{width:38px;height:38px;background:{'#1A1A1A' if dm else '#F3F4F6'};border:1px solid {'#333' if dm else '#E5E7EB'};border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:22px;color:{TC};cursor:pointer;user-select:none;flex-shrink:0;}}
.wel{{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:50px 20px;text-align:center;}}
.wl{{width:80px;height:80px;background:linear-gradient(135deg,#4338CA,#7C3AED);border-radius:24px;
    display:flex;align-items:center;justify-content:center;font-size:42px;margin-bottom:16px;
    box-shadow:0 8px 30px rgba(99,102,241,0.4);}}
.wn{{font-size:26px;font-weight:800;margin-bottom:10px;
    background:linear-gradient(135deg,#4F46E5,#7C3AED,#EC4899);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;}}
.uw{{display:flex;justify-content:flex-end;padding:5px 0;}}
.um{{background:linear-gradient(135deg,#4F46E5,#7C3AED);color:white;padding:12px 16px;
    border-radius:18px 18px 4px 18px;max-width:78%;font-size:14px;line-height:1.6;
    box-shadow:0 4px 12px rgba(99,102,241,0.3);}}
.ut{{font-size:11px;color:rgba(255,255,255,0.6);margin-top:4px;text-align:right;}}
.aw{{display:flex;gap:10px;align-items:flex-start;padding:5px 0;}}
.aa{{width:34px;height:34px;background:linear-gradient(135deg,#4338CA,#7C3AED);border-radius:50%;
    display:flex;align-items:center;justify-content:center;font-size:15px;flex-shrink:0;margin-top:2px;}}
.ac{{flex:1;max-width:86%;}}
.am{{background:{MSGBG};border:1px solid {MSGBD};color:{MSGC};padding:12px 16px;
    border-radius:4px 18px 18px 18px;font-size:14px;line-height:1.7;}}
.at{{font-size:11px;color:#555;margin-top:4px;}}
.cb{{background:#0D1117;border:1px solid #30363D;border-radius:8px;margin:10px 0;overflow:hidden;}}
.ch{{background:#161B22;padding:8px 14px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #30363D;}}
.cl{{font-size:12px;color:#8B949E;font-family:monospace;}}
.cb pre{{margin:0;padding:14px;overflow-x:auto;font-size:13px;line-height:1.6;color:#E6EDF3;font-family:'Courier New',monospace;}}
.cpb{{background:#1A1A1A;border:1px solid #2A2A2A;color:#888;padding:4px 10px;border-radius:6px;font-size:12px;cursor:pointer;}}
section[data-testid="stBottom"]{{background:{BOTBG}!important;}}
section[data-testid="stBottom"] > div{{background:{BOTBG}!important;}}
[data-testid="stChatInputContainer"]{{background:{BOTBG}!important;border-top:1px solid {'#1E1E1E' if dm else '#E5E7EB'}!important;}}
.stChatInput textarea{{background:{INBG}!important;color:{INC}!important;border:1px solid {'#2A2A2A' if dm else '#D1D5DB'}!important;border-radius:14px!important;font-size:14px!important;}}
.stChatInput textarea:focus{{border-color:#4F46E5!important;}}
[data-testid="stChatInputSubmitButton"]{{background:linear-gradient(135deg,#4F46E5,#7C3AED)!important;border-radius:10px!important;}}
.td{{display:flex;gap:4px;align-items:center;padding:8px 0;}}
.td div{{width:8px;height:8px;background:#4F46E5;border-radius:50%;animation:td 1.2s infinite;}}
.td div:nth-child(2){{animation-delay:0.2s;}}
.td div:nth-child(3){{animation-delay:0.4s;}}
@keyframes td{{0%,60%,100%{{opacity:0.2;transform:scale(0.8);}}30%{{opacity:1;transform:scale(1);}}}}
div[data-testid="stFileUploader"] label{{display:none!important;}}
.stMarkdown p{{color:{MSGC}!important;}}
.block-container{{padding-top:0!important;max-width:100%!important;padding-left:0.8rem!important;padding-right:0.8rem!important;}}
</style>
""", unsafe_allow_html=True)

# ── CHAT LIST & EXPORT FOR PANEL ──────────────────────────────────────────────
chat_list_html = ""
for cid2, cd2 in sorted(st.session_state.chats.items(), key=lambda x: x[1]["created_at"], reverse=True):
    t2 = html_lib.escape(cd2.get("title","New Chat")[:28])
    act2 = "background:#1E1B4B;color:#A5B4FC;border-color:#4F46E5;" if cid2 == st.session_state.cid else ""
    chat_list_html += "<div style='display:flex;align-items:center;gap:8px;padding:9px 12px;border-radius:8px;cursor:pointer;font-size:13px;margin-bottom:2px;border:1px solid transparent;color:#999;" + act2 + "' onclick=\"location.href=location.pathname+\'?action=sw_" + cid2 + "\'\">💬 " + t2 + "</div>" 

exp_links = ""
if st.session_state.cid and st.session_state.cid in st.session_state.chats:
    cc2 = st.session_state.chats[st.session_state.cid]
    if cc2.get("messages"):
        et2 = f"Bharat AI Chat\n{get_india_time().strftime('%d %B %Y')}\n\n"
        for m2 in cc2["messages"]:
            et2 += f"[{'You' if m2['role']=='user' else 'Bharat AI'}]\n{m2['content']}\n\n"
        b64t2 = base64.b64encode(et2.encode()).decode()
        ds2 = get_india_time().strftime('%d%m%Y')
        exp_links += "<a href='data:text/plain;base64," + b64t2 + "' download='chat_" + ds2 + ".txt' style='display:flex;align-items:center;gap:8px;padding:10px 14px;border-radius:10px;border:1px solid #2A2A2A;color:#fff;text-decoration:none;font-size:13px;margin-bottom:8px;'>📝 TXT Download</a>" 
        try:
            pdf2 = create_pdf(et2, cc2.get("title","Bharat AI"))
            b64p2 = base64.b64encode(pdf2).decode()
            exp_links += "<a href='data:application/pdf;base64," + b64p2 + "' download='chat_" + ds2 + ".pdf' style='display:flex;align-items:center;gap:8px;padding:10px 14px;border-radius:10px;border:1px solid #2A2A2A;color:#fff;text-decoration:none;font-size:13px;margin-bottom:8px;'>📄 PDF Download</a>" 
        except: pass

mode_lbl2 = "☀️ Light Mode" if dm else "🌙 Dark Mode"
SC2 = "#888" if dm else "#555"
PBG2 = "#141414" if dm else "#fff"
TC2 = "#fff" if dm else "#111"
PBD2 = "#2A2A2A" if dm else "#E5E7EB"

# ── HEADER ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class='panel-overlay' id='pov' onclick='closePanel()'></div>

<div class='side-panel' id='spnl'>
    <div style='display:flex;align-items:center;justify-content:space-between;padding:14px 16px;border-bottom:1px solid {PBD2};position:sticky;top:0;background:{PBG2};z-index:10;'>
        <div style='display:flex;align-items:center;gap:10px;'>
            <div style='width:36px;height:36px;background:linear-gradient(135deg,#4338CA,#7C3AED);border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:17px;'>⚡</div>
            <div>
                <div style='font-size:15px;font-weight:700;color:{TC2};'>Bharat AI ✨</div>
                <div style='font-size:11px;color:{SC2};'>Aapka AI Saathi</div>
            </div>
        </div>
        <div onclick='closePanel()' style='width:28px;height:28px;background:#2A2A2A;border-radius:50%;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:13px;color:{TC2};'>✕</div>
    </div>

    <div style='padding:10px 14px;'>
        <div onclick="location.href=location.pathname+'?action=new_chat'" style='display:flex;align-items:center;justify-content:center;padding:11px;border-radius:10px;background:linear-gradient(135deg,#4F46E5,#7C3AED);color:#fff;cursor:pointer;font-size:14px;font-weight:700;margin-bottom:8px;'>＋ New Chat</div>
        <div style='background:#1A1A1A;border:1px solid {PBD2};border-radius:10px;padding:10px 14px;display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;'>
            <div><div style='font-size:11px;color:{SC2};'>Aaj ke messages</div><div style='font-size:16px;font-weight:700;color:#A5B4FC;'>{st.session_state.msg_count}/1500</div></div>
            <div style='font-size:24px;'>💬</div>
        </div>
        <div onclick="location.href=location.pathname+'?action=toggle_mode'" style='display:flex;align-items:center;gap:8px;padding:10px 14px;border-radius:10px;border:1px solid {PBD2};color:{TC2};cursor:pointer;font-size:13px;margin-bottom:8px;'>{mode_lbl2}</div>
        <div onclick="location.href=location.pathname+'?action=clear_chat'" style='display:flex;align-items:center;gap:8px;padding:10px 14px;border-radius:10px;border:1px solid {PBD2};color:{TC2};cursor:pointer;font-size:13px;margin-bottom:8px;'>🗑️ Clear Chat</div>
        <div onclick="location.href=location.pathname+'?action=delete_chat'" style='display:flex;align-items:center;gap:8px;padding:10px 14px;border-radius:10px;border:1px solid #3A1A1A;color:#EF4444;cursor:pointer;font-size:13px;margin-bottom:8px;'>🔴 Delete Chat</div>
    </div>

    <div style='padding:0 14px;'>
        <div style='font-size:10px;font-weight:700;color:{SC2};text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;'>Export</div>
        {exp_links if exp_links else f"<div style='font-size:12px;color:#555;'>Pehle chat karo</div>"}
    </div>

    <hr style='border:none;border-top:1px solid {PBD2};margin:8px 0;'>

    <div style='padding:0 14px;'>
        <div style='font-size:10px;font-weight:700;color:{SC2};text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;'>Recent Chats</div>
        <input type='text' placeholder='🔍 Search...' oninput='filterC(this.value)' style='width:100%;padding:8px 10px;background:#1A1A1A;border:1px solid {PBD2};border-radius:8px;color:{TC2};font-size:12px;margin-bottom:8px;outline:none;box-sizing:border-box;'>
        <div id='clist'>{chat_list_html}</div>
    </div>

    <div style='background:#1A1A1A;border:1px solid {PBD2};border-radius:12px;padding:14px;text-align:center;margin:12px 14px;'>
        <div style='font-size:22px;margin-bottom:6px;'>🤖</div>
        <div style='font-size:13px;font-weight:700;color:#A5B4FC;'>Bharat AI</div>
        <div style='font-size:11px;color:{SC2};line-height:1.8;'>by Bharat Pritmani<br>Jaipur 🇮🇳<br><span style='color:#4F46E5;'>Gemini 2.5 Flash</span></div>
    </div>
</div>

<div class='hdr'>
    <div style='display:flex;align-items:center;gap:10px;'>
        <div class='h-av'>⚡</div>
        <div>
            <div class='h-name'>Bharat AI ✨</div>
            <div class='h-dot'>Online</div>
        </div>
    </div>
    <button onclick='openPanel()' style='width:38px;height:38px;background:#1A1A1A;border:1px solid #333;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:22px;color:#fff;cursor:pointer;flex-shrink:0;'>⋮</button>
</div>

<script>
function openPanel(){{
    document.getElementById('spnl').classList.add('open');
    document.getElementById('pov').classList.add('open');
}}
function closePanel(){{
    document.getElementById('spnl').classList.remove('open');
    document.getElementById('pov').classList.remove('open');
}}
function filterC(q){{
    document.querySelectorAll('#clist > div').forEach(function(el){{
        el.style.display = el.textContent.toLowerCase().includes(q.toLowerCase()) ? 'flex' : 'none';
    }});
}}
</script>
""", unsafe_allow_html=True)

# ── IMAGE UPLOAD ───────────────────────────────────────────────────────────────
if st.session_state.uploaded_image is None:
    with st.expander("📷 Image Upload karo", expanded=False):
        upl = st.file_uploader("img", type=["jpg","jpeg","png"], key="img_upload", label_visibility="collapsed")
        if upl: st.session_state.uploaded_image = upl; st.rerun()
else:
    c1,c2,c3 = st.columns([1,3,1])
    with c1: st.image(st.session_state.uploaded_image.getvalue(), width=60)
    with c2: st.caption(f"📎 {st.session_state.uploaded_image.name[:20]}")
    with c3:
        if st.button("❌", key="rm_img"): st.session_state.uploaded_image = None; st.rerun()

# ── WELCOME SCREEN ─────────────────────────────────────────────────────────────
if not st.session_state.cid or st.session_state.cid not in st.session_state.chats:
    h_now = get_india_time().hour
    if 5<=h_now<12:    ge,gt,gc="🌅","Good Morning,","#FF9A3C"
    elif 12<=h_now<17: ge,gt,gc="☀️","Good Afternoon,","#FFD700"
    elif 17<=h_now<21: ge,gt,gc="🌆","Good Evening,","#FF6B6B"
    else:              ge,gt,gc="🌙","Good Night,","#A78BFA"
    st.markdown(f"""
    <div class='wel'>
        <div class='wl'>{ge}</div>
        <div style='font-size:20px;font-weight:700;color:{gc};margin-bottom:4px;'>{gt}</div>
        <div class='wn'>Bharat! 🙏</div>
        <div style='font-size:14px;font-weight:600;color:{"#FFF" if dm else "#111"};margin-bottom:6px;'>Main Bharat AI hoon ⚡</div>
        <div style='font-size:13px;color:{SC};'>Kuch likho — chat shuru ho jaayegi!</div>
    </div>""", unsafe_allow_html=True)

# ── MESSAGES ───────────────────────────────────────────────────────────────────
if st.session_state.cid and st.session_state.cid in st.session_state.chats:
    cc = st.session_state.chats[st.session_state.cid]
    for i, msg in enumerate(cc["messages"]):
        ts = msg.get("timestamp","")
        if msg["role"] == "user":
            ib = "📷 " if msg.get("has_image") else ""
            st.markdown(f"""<div class='uw'><div>
                <div class='um'>{ib}{html_lib.escape(msg['content'])}</div>
                <div class='ut'>{ts} <span style='color:#A5B4FC;'>✓✓</span></div>
            </div></div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div class='aw'>
                <div class='aa'>⚡</div>
                <div class='ac'>
                    <div class='am'>{fmt_msg(msg['content'])}</div>
                    <div class='at'>{ts}</div>
                </div>
            </div>""", unsafe_allow_html=True)
            if i > 0 and cc["messages"][i-1].get("export_requested"):
                sk = ts.replace(":","").replace(" ","")
                dls = ""
                try:
                    pdf = create_pdf(msg["content"], cc.get("title","Bharat AI"))
                    dls += dl_link(pdf, f"bharat_{sk}.pdf", "📄 PDF Download", "application/pdf")
                except: pass
                try:
                    dls += dl_link(msg["content"].encode(), f"bharat_{sk}.txt", "📝 TXT Download", "text/plain")
                except: pass
                if dls: st.markdown(f"<div style='padding:4px 0;'>{dls}</div>", unsafe_allow_html=True)

# ── CHAT INPUT ─────────────────────────────────────────────────────────────────
if st.session_state.uploaded_image:
    st.info(f"📷 Image ready: **{st.session_state.uploaded_image.name}**")

prompt = st.chat_input("Message Bharat AI...")
if prompt:
    # Agar koi chat nahi — naya banao
    if not st.session_state.cid or st.session_state.cid not in st.session_state.chats:
        nid = str(uuid.uuid4())
        st.session_state.chats[nid] = {"title": prompt[:30], "messages":[], "created_at":get_india_time()}
        st.session_state.cid = nid
        save_chats()

    cc = st.session_state.chats[st.session_state.cid]
    if cc["title"]=="New Chat" and not cc["messages"]:
        cc["title"] = prompt[:30]+("..." if len(prompt)>30 else "")

    now_str = get_india_time().strftime("%I:%M %p")
    has_img = st.session_state.uploaded_image is not None
    cc["messages"].append({"role":"user","content":prompt,"timestamp":now_str,
        "has_image":has_img,"export_requested":needs_export(prompt)})
    st.session_state.msg_count += 1

    try:
        tp = st.empty()
        tp.markdown("<div class='aw'><div class='aa'>⚡</div><div class='td'><div></div><div></div><div></div></div></div>", unsafe_allow_html=True)
        hist = [{"role":"user" if m["role"]=="user" else "model","parts":[m["content"]]} for m in cc["messages"][:-1]]
        fs = get_model().start_chat(history=hist)
        if has_img:
            imgf = st.session_state.uploaded_image
            ib = imgf.getvalue()
            mt = "image/jpeg" if imgf.name.lower().endswith((".jpg",".jpeg")) else "image/png"
            response = fs.send_message([{"inline_data":{"mime_type":mt,"data":base64.b64encode(ib).decode()}}, prompt])
            st.session_state.uploaded_image = None
        else:
            response = fs.send_message(prompt)
        ar = ""
        try:
            for part in response.candidates[0].content.parts:
                if hasattr(part,'text') and part.text: ar += part.text
            if not ar: ar = response.text
        except:
            try: ar = response.text
            except: ar = "Kuch error aa gaya, dobara try karo! 😅"
        cc["messages"].append({"role":"assistant","content":ar,"timestamp":get_india_time().strftime("%I:%M %p")})
        save_chats(); tp.empty(); st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")
