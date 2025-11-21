# dsa_chatbot.py
import streamlit as st
from groq import Groq
import os
import io
import uuid
from typing import List, Dict
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
import datetime

# -------------------------
# CONFIG
# -------------------------
MAX_HISTORY = 12  # last N messages to include as context
GROQ_MODEL = "llama-3.1-8b-instant"

# Fallback hardcoded key for local testing only (avoid in production)
GROQ_API_KEY_HARDCODED = "REMOVED_SECRETibMT7L71iLq3z23UlE5UWGdyb3FYwB8GTKH0PfoitsYJmBfJWNlQ"

# Optional font for Devanagari/Hindi
FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")
FONT_PATH = os.path.join(FONT_DIR, "NotoSansDevanagari-Regular.ttf")

# -------------------------
# SYSTEM PROMPT
# -------------------------
SYSTEM_PROMPT = """ 
You are "DSA Dost" — an expert, friendly tutor for Data Structures & Algorithms. 
Your replies MUST be grammatically correct, clear, and well-formed sentences. Avoid broken Hindi, fractured English, slang, or filler. Use a balanced Hinglish style: technical definitions in clear English, short explanatory sentences in simple Hindi. Never reply completely in only Hindi or only English.

Tone & Style:
- Friendly, encouraging, and concise. Use 1–3 short sentences per idea.
- Use phrases like "Mast question!" occasionally, but do NOT overuse them.
- Avoid repeating the same sentence or phrase across replies.
- If the user repeats the same question, give a fresh analogy or example — do not reuse old text verbatim.

Answer Structure (always follow this order):
1. **Definition (1–2 sentences in English, exam-friendly).**
2. **Short Explanation (2–4 sentences in simple Hinglish; use an analogy).**
3. **Offer next step question:** Ask either "Example chahiye?" or "Code dekhna hai?" — only one short question. If the user explicitly asks for code or example, provide it immediately.

Code & Examples:
- Default language for code examples: **C++**. If the user requests another language (Python, Java, JavaScript), switch.
- Provide clean, tested, and commented code snippets.
- Include **Time & Space complexity** when answering algorithmic/code questions.

Formatting rules:
- Use bullet points or numbered steps only when it improves clarity.
- For math or algorithms, include complexity in Big-O notation.
- For multi-line code in text outputs or PDFs, preserve formatting and use monospace.

Memory & Conversation:
- Maintain short-term conversation context to answer follow-ups.
- If necessary for a correct technical answer, reference previous user messages — but do not repeat entire history unless asked.
- If the user asks "what did I ask earlier?" summarize the previous message(s) concisely.

Error handling & Out-of-scope:
- If asked about non-DSA topics, politely refuse: "Yaar, ye DSA se bahar hai. Main DSA mein madad kar sakta hoon — koi DSA sawaal pucho."
- If you don't know an answer, reply: "Example me abhi beta version hu. I am under development." and offer to search (if allowed).
- Keep error messages polite and actionable (e.g., "Sorry, mujhe iske liye aur info chahiye — kya aap input / constraints de sakte ho?").

Politeness & brevity:
- Keep replies compact. If the topic is large, provide a short summary + offer to expand.
- Avoid long paragraphs — prefer short readable lines.

Example reply format for "What is a Stack?":
Definition: "A stack is a LIFO (Last-In-First-Out) data structure used to store elements temporarily."
Explanation: "Samjho shaadi ki plates ka dher — jo plate sabse upar rakhi usse pehle uthayi jaati hai. Push se add hota hai, pop se remove hota hai."
Offer: "Example chahiye? Code dekhna hai iska?"

Language constraint:
- Use ONLY English and Hindi. No other languages allowed.


"""

# -------------------------
# Secrets helper
# -------------------------
def get_secret(key_path: List[str], default=None):
    """Try st.secrets then env var fallback."""
    try:
        node = st.secrets
        for k in key_path:
            node = node[k]
        return node
    except Exception:
        env_key = "_".join(key_path).upper()
        return os.getenv(env_key, default)

# Groq API key preference: Streamlit secrets -> env -> hardcoded
GROQ_API_KEY = get_secret(["groq", "api_key"], None) or os.getenv("GROQ_API_KEY") or GROQ_API_KEY_HARDCODED

# -------------------------
# PDF helpers (reportlab)
# -------------------------
def register_font():
    """Register a Devanagari TTF if present; return font name or None."""
    try:
        if os.path.isfile(FONT_PATH):
            pdfmetrics.registerFont(TTFont("NotoDeva", FONT_PATH))
            return "NotoDeva"
    except Exception as e:
        print("Font register failed:", e)
    return None

def create_chat_pdf_bytes(messages: List[Dict], title: str = "DSA Chat History") -> bytes:
    """
    messages: list of dicts {role, content, created_at (optional)}
    returns bytes of generated PDF.
    """
    font_name = register_font()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    if font_name:
        base_style = ParagraphStyle("Base", parent=styles["Normal"], fontName=font_name, fontSize=11, leading=14)
        title_style = ParagraphStyle("Title", parent=styles["Title"], fontName=font_name, fontSize=16, leading=20)
    else:
        base_style = styles["Normal"]
        title_style = styles["Title"]

    story = []
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"Exported on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", base_style))
    story.append(Spacer(1, 8))

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        created_at = msg.get("created_at", "")
        label = "<b>You:</b> " if role == "user" else "<b>Bot:</b> "
        ts = f" <font size=8 color=grey>({created_at})</font>" if created_at else ""
        ptext = f"{label}{content}{ts}"
        story.append(Paragraph(ptext, base_style))
        story.append(Spacer(1, 6))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

# -------------------------
# Initialize Groq client
# -------------------------
if not GROQ_API_KEY:
    st.error("GROQ_API_KEY not set. Put it in Streamlit secrets (~/.streamlit/secrets.toml) or set GROQ_API_KEY env var.")
    st.stop()

try:
    groq_client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    st.error(f"Failed to initialize Groq client: {e}")
    st.stop()

# -------------------------
# Streamlit UI & Session
# -------------------------
st.set_page_config(page_title="DSA Assistant Chatbot", layout="centered")
st.title("🤖 AI DSA Chatbot (History + PDF Export)")
st.caption("Chat history is temporary (session-based). Use download to save a PDF copy.")

# create per-tab session id
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
session_id = st.session_state.session_id

# show uploaded image (developer note: this uses the uploaded file path)
# The file path from your upload is displayed as image in sidebar (will be transformed to URL in the environment)
uploaded_image_path = "/mnt/data/8f9abd23-4f26-4a6a-a3da-e9c8731aaf59.png"
if os.path.isfile(uploaded_image_path):
    st.sidebar.image(uploaded_image_path, caption="Uploaded screenshot", use_column_width=True)

st.sidebar.markdown(f"**Session id:** `{session_id}`")
st.sidebar.markdown("---")
st.sidebar.markdown("### Export / Actions")

# initialize messages in session_state (temporary storage only)
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! Main aapka AI-DSA Assistant hoon. Mujhse koi bhi DSA-related sawal poochein, jaise Binary Search ya Merge Sort.", "created_at": ""}
    ]

# Display messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Prepare pdf messages (from session_state)
def prepare_pdf_messages():
    pdf_msgs = []
    for m in st.session_state.get("messages", []):
        pdf_msgs.append({
            "role": m.get("role"),
            "content": m.get("content"),
            "created_at": m.get("created_at", "")
        })
    return pdf_msgs

# Download button (creates PDF on demand)
def get_pdf_bytes_for_download():
    msgs = prepare_pdf_messages()
    return create_chat_pdf_bytes(msgs, title="DSA Dost - Chat Export (Temporary)")

st.sidebar.download_button(
    label="Download full chat as PDF.",
    data=get_pdf_bytes_for_download(),
    file_name="dsa_chat_history.pdf",
    mime="application/pdf"
)

# Clear local session chat (not DB)
if st.sidebar.button("Clear chat"):
    st.session_state.messages = []
    # rerun to refresh UI
    st.rerun()

# -------------------------
# Chat input handling (no DB)
# -------------------------
if prompt := st.chat_input("Apna DSA sawal yahan poochein..."):
    # append user message locally
    created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.messages.append({"role": "user", "content": prompt, "created_at": created_at})
    with st.chat_message("user"):
        st.markdown(prompt)

    # build context for API: send system + last MAX_HISTORY turns
    conversation_history = []
    for msg in st.session_state.messages[-MAX_HISTORY:]:
        if msg["role"] in ["user", "assistant"]:
            conversation_history.append({"role": msg["role"], "content": msg["content"]})

    groq_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history

    # call Groq
    try:
        with st.chat_message("assistant"):
            with st.spinner("Assistant is typing..."):
                chat_completion = groq_client.chat.completions.create(
                    messages=groq_messages,
                    model=GROQ_MODEL,
                )
                ai_response = chat_completion.choices[0].message.content
                # show response
                st.markdown(ai_response)

        # append assistant response locally
        resp_created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.messages.append({"role": "assistant", "content": ai_response, "created_at": resp_created_at})

    except Exception as e:
        st.error(f"Groq se response fetch karne mein error: {e}")
        err_msg = "Error: Response fetch nahi ho paya. Please try again."
        st.session_state.messages.append({"role": "assistant", "content": err_msg, "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
