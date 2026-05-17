import streamlit as st
import google.generativeai as genai
import os

# 1 AMIR── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MediBot – AI Health Assistant",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg:          #0d1117;
    --surface:     #161b22;
    --surface2:    #1c2330;
    --border:      #30363d;
    --accent:      #4285f4;
    --accent-soft: #1a3a6e;
    --warn:        #f85149;
    --warn-soft:   #3d1f1e;
    --amber:       #e3b341;
    --amber-soft:  #3d2e0e;
    --text:        #e6edf3;
    --muted:       #8b949e;
    --user-bubble: #1f3a5f;
    --bot-bubble:  #161b22;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: var(--bg);
    color: var(--text);
}
h1, h2, h3 { font-family: 'DM Serif Display', serif; }

#MainMenu, footer, header { visibility: hidden; }

section[data-testid="stSidebar"] {
    background: var(--surface);
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] .stMarkdown p {
    color: var(--muted);
    font-size: 0.85rem;
}

.chat-wrapper { display: flex; flex-direction: column; gap: 1rem; padding-bottom: 6rem; }

.msg-row { display: flex; gap: 0.75rem; align-items: flex-start; }
.msg-row.user { flex-direction: row-reverse; }

.avatar {
    width: 36px; height: 36px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem; flex-shrink: 0;
}
.avatar.bot  { background: var(--accent-soft); border: 1px solid var(--accent); }
.avatar.user { background: var(--user-bubble); border: 1px solid #2d5a99; }

.bubble {
    max-width: 72%;
    padding: 0.85rem 1.1rem;
    border-radius: 1rem;
    line-height: 1.65;
    font-size: 0.95rem;
}
.bubble.bot {
    background: var(--bot-bubble);
    border: 1px solid var(--border);
    border-top-left-radius: 0.2rem;
}
.bubble.user {
    background: var(--user-bubble);
    border: 1px solid #2d5a99;
    border-top-right-radius: 0.2rem;
}

.warn-card {
    background: var(--warn-soft);
    border: 1px solid var(--warn);
    border-radius: 0.6rem;
    padding: 0.6rem 0.9rem;
    margin-top: 0.5rem;
    font-size: 0.82rem;
    color: #ffa198;
}
.info-card {
    background: var(--amber-soft);
    border: 1px solid var(--amber);
    border-radius: 0.6rem;
    padding: 0.6rem 0.9rem;
    margin-top: 0.5rem;
    font-size: 0.82rem;
    color: #f0c060;
}

.stChatInput textarea {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 0.75rem !important;
}
.stChatInput textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(66,133,244,0.15) !important;
}

.stSelectbox select, div[data-baseweb="select"] {
    background: var(--surface2) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
}
.stButton button {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 0.5rem;
    transition: border-color .2s;
}
.stButton button:hover { border-color: var(--accent) !important; }

.chip {
    display: inline-block;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 2rem;
    padding: 0.25rem 0.7rem;
    font-size: 0.78rem;
    color: var(--muted);
    margin: 0.15rem;
}
</style>
""", unsafe_allow_html=True)

# ── Language config ───────────────────────────────────────────────────────────
LANGUAGES = {
    "English":   "en",
    "العربية":   "ar",
    "Español":   "es",
    "Français":  "fr",

}

LANG_PROMPTS = {
    "en": "Respond in English.",
    "ar": "أجب باللغة العربية.",
    "es": "Responde en español.",
    "fr": "Réponds en français.",

}

SYSTEM_PROMPT = """You are MediBot, a compassionate and knowledgeable AI medical assistant powered by Google Gemini.

Your goals:
1. Help users understand their symptoms clearly and empathetically.
2. Suggest possible conditions/diseases that match the described symptoms (always list 2-4 possibilities with brief explanations).
3. Provide practical, evidence-based basic medical advice (home care, when to rest, hydration, OTC options etc.).
4. Ask clarifying follow-up questions when symptoms are vague.
5. Always remind users to consult a real healthcare professional for diagnosis and treatment.

Output format (use markdown):
- Use **bold** for key terms and condition names.
- Use bullet lists for symptom breakdowns and advice steps.
- Include a ⚠️ WARNING section at the end if symptoms could indicate a serious/emergency condition.
- Include a 💡 GENERAL ADVICE section with actionable home-care tips.
- Keep tone warm, clear, and non-alarmist unless the situation truly warrants urgency.

IMPORTANT DISCLAIMERS to embed naturally:
- You are NOT a substitute for professional medical advice.
- Never recommend specific prescription medications.
- Always direct emergencies (chest pain, difficulty breathing, severe bleeding, loss of consciousness) to call emergency services immediately.

{lang_instruction}
"""

# ── Helper: get API key ─────────────────────────────────────────────────────── #0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
def get_api_key():
    # Priority: session state input → st.secrets → environment variable
    if st.session_state.get("user_api_key"):
        return st.session_state["user_api_key"]
    try:
        return st.secrets["GOOGLE_API_KEY"]
    except Exception:
        pass
    return os.environ.get("GOOGLE_API_KEY", "")


# ── Helper: build Gemini model ────────────────────────────────────────────────
def build_model(api_key: str, lang_code: str):
    genai.configure(api_key=api_key)
    system = SYSTEM_PROMPT.format(lang_instruction=LANG_PROMPTS.get(lang_code, ""))
    return genai.GenerativeModel(
        model_name="gemini-2.5-flash-lite",
        system_instruction=system,
        generation_config=genai.types.GenerationConfig(
            max_output_tokens=1024,
            temperature=0.7,
        ),
    )


#2 ABDULAH ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🩺 MediBot")
    st.markdown("*Powered by **Google Gemini***")
    st.divider()

    existing_key = get_api_key()
    if existing_key:
        st.markdown(
            "<div class='info-card'>✅ Google API key is set</div>",
            unsafe_allow_html=True,
        )
    else:
        typed_key = st.text_input(
            "🔑 Google API Key",
            type="password",
            placeholder="AIza...",
            help="Get yours free at https://aistudio.google.com/app/apikey",
        )
        if typed_key:
            st.session_state["user_api_key"] = typed_key
            st.success("API key saved for this session ✓")
            st.rerun()

    st.divider()

    lang_choice = st.selectbox(
        "🌐 Language / اللغة",
        list(LANGUAGES.keys()),
        index=0,
    )
    lang_code = LANGUAGES[lang_choice]

    st.divider()
    st.markdown("#### About")
    st.markdown("""
MediBot uses **Google Gemini 2.5 Flash** to help you:
- Understand your symptoms
- Explore possible conditions
- Get basic home-care advice

**Always consult a doctor** for proper diagnosis.
    """)

    st.divider()
    if st.button("🗑️ Clear conversation"):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.markdown("""
<div style='font-size:0.75rem; color:#8b949e;'>
⚠️ <strong>Disclaimer</strong><br>
MediBot is for informational purposes only.
It does not provide medical diagnosis or replace
professional healthcare advice. In emergencies,
call your local emergency number immediately.
</div>
""", unsafe_allow_html=True)

#3 ABDELRAHMAN── Main header ───────────────────────────────────────────────────────────────
col_head, col_badge = st.columns([5, 1])
with col_head:
    st.markdown("# MediBot")
    st.markdown(
        "<p style='color:#8b949e; margin-top:-0.5rem;'>Describe your symptoms and I'll help you understand them.</p>",
        unsafe_allow_html=True,
    )
with col_badge:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"<span class='chip'>🌐 {lang_choice}</span>", unsafe_allow_html=True)

st.markdown("""
<div class='warn-card'>
⚠️ <strong>Medical Disclaimer:</strong> MediBot is not a licensed physician.
Information provided is for educational purposes only.
<strong>Call emergency services if you have chest pain, trouble breathing, or any life-threatening symptoms.</strong>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

#4 ── STEVIN Render message helper ─────────────────────────────────────────────────────
def render_message(role: str, content: str, use_md: bool = False):
    if role == "assistant":
        st.markdown("""
<div class='msg-row bot'>
  <div class='avatar bot'>🩺</div>
  <div class='bubble bot'>""", unsafe_allow_html=True)
        if use_md:
            st.markdown(content)
        else:
            st.markdown(content, unsafe_allow_html=True)
        st.markdown("</div></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"""
<div class='msg-row user'>
  <div class='avatar user'>👤</div>
  <div class='bubble user'>{content}</div>
</div>""", unsafe_allow_html=True)

# ── Chat display ──────────────────────────────────────────────────────────────
st.markdown("<div class='chat-wrapper'>", unsafe_allow_html=True)

if not st.session_state.messages:
    st.markdown("""
<div class='msg-row bot'>
  <div class='avatar bot'>🩺</div>
  <div class='bubble bot'>
    Hello! I'm <strong>MediBot</strong>, your AI health assistant powered by <strong>Google Gemini</strong>. 👋<br><br>
    Please describe your symptoms in as much detail as you can —
    how long you've had them, their severity, and any other relevant information.<br><br>
    <em>Remember: I'm here to help you understand your symptoms, but always consult a doctor for a proper diagnosis.</em>
  </div>
</div>
""", unsafe_allow_html=True)

for msg in st.session_state.messages:
    render_message(msg["role"], msg["content"], use_md=(msg["role"] == "assistant"))

st.markdown("</div>", unsafe_allow_html=True)

#5 KERO ── Chat input ────────────────────────────────────────────────────────────────
if user_input := st.chat_input("Describe your symptoms here…"):

    api_key = get_api_key()
    if not api_key:
        st.error("⚠️ Please enter your Google API Key in the sidebar to continue.")
        st.stop()

    # Save & show user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    render_message("user", user_input)

    with st.spinner("Analyzing your symptoms with Gemini…"):
        try:
            model = build_model(api_key, lang_code)

            # Rebuild Gemini-format history (roles: "user" | "model")
            gemini_history = []
            for m in st.session_state.messages[:-1]:  # exclude current user msg
                g_role = "model" if m["role"] == "assistant" else "user"
                gemini_history.append({"role": g_role, "parts": [m["content"]]})

            chat = model.start_chat(history=gemini_history)
            response = chat.send_message(user_input)
            reply = response.text

        except Exception as e:
            reply = f"⚠️ Error connecting to Gemini: {e}"

    st.session_state.messages.append({"role": "assistant", "content": reply})
    render_message("assistant", reply, use_md=True)
    st.rerun()
