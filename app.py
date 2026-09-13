import json
import streamlit.components.v1 as components
import os
import streamlit as st
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from dotenv import load_dotenv
from google import genai
from google.genai import types
from database import (
    init_db, create_conversation, get_conversations,
    rename_conversation, save_message, load_messages, delete_conversation
)

def copy_button(text, button_id):
    """Render a small button that copies the given text to the clipboard."""
    escaped_text = json.dumps(text)
    html_code = f"""
    <button id="copy-btn-{button_id}"
        style="font-size:12px; padding:3px 10px; cursor:pointer;
               border-radius:6px; border:1px solid #ccc; background:#f0f0f2;">
        Copy
    </button>
    <script>
        document.getElementById("copy-btn-{button_id}").addEventListener("click", function() {{
            navigator.clipboard.writeText({escaped_text});
        }});
    </script>
    """
    components.html(html_code, height=35)

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

init_db()

st.set_page_config(page_title="Byte - AI Chatbot", page_icon="🤖")

if not api_key:
    st.error("GEMINI_API_KEY not found. Check your .env file.")
    st.stop()

PERSONALITIES = {
    "Sarcastic Mentor (default)": "You are a witty, slightly sarcastic coding mentor named Byte. Keep answers short and add a joke when it fits.",
    "Strict Professor": "You are a strict, no-nonsense computer science professor named Byte. Be precise, formal, and focus on correctness over friendliness.",
    "Chill Friend": "You are a laid-back, encouraging friend named Byte who happens to know a lot about coding. Keep things casual and supportive.",
    "Motivational Coach": "You are an energetic, motivational coach named Byte who helps people push through coding struggles with hype and encouragement.",
}
if "selected_personality" not in st.session_state:
    st.session_state.selected_personality = list(PERSONALITIES.keys())[0]


# Default system instruction used when creating the Gemini chat session.
SYSTEM_INSTRUCTION = PERSONALITIES["Sarcastic Mentor (default)"]

# Create the Gemini client once per session (doesn't depend on which conversation is open)
if "client" not in st.session_state:
    st.session_state.client = genai.Client(api_key=api_key)

# On first load, either open the most recent conversation or start a new one
if "current_conversation_id" not in st.session_state:
    conversations = get_conversations()
    if conversations:
        st.session_state.current_conversation_id = conversations[0]["id"]
    else:
        st.session_state.current_conversation_id = create_conversation()

def load_conversation(conversation_id):
    """Switch the active chat session to a given conversation, replaying its history."""
    st.session_state.current_conversation_id = conversation_id
    messages = load_messages(conversation_id)

    formatted_history = [
        types.Content(
            role="model" if msg["role"] == "assistant" else "user",
            parts=[types.Part.from_text(text=msg["content"])]
        )
        for msg in messages
    ]

    instruction = PERSONALITIES[st.session_state.selected_personality]

    st.session_state.chat = st.session_state.client.chats.create(
        model="gemini-3.6-flash",
        history=formatted_history,
        config=types.GenerateContentConfig(system_instruction=instruction)
    )
    st.session_state.messages = messages
    st.session_state.active_personality = st.session_state.selected_personality

# Build the active chat session if we haven't yet (first run, or after switching conversations)
if "chat" not in st.session_state:
    load_conversation(st.session_state.current_conversation_id)

# If the user picked a different personality than what's currently active, rebuild the session
elif st.session_state.get("active_personality") != st.session_state.selected_personality:
    load_conversation(st.session_state.current_conversation_id)
# ---- SIDEBAR ----
with st.sidebar:
    st.header("💬 Conversations")
    selected_personality = st.selectbox(
        "Byte's personality",
        options=list(PERSONALITIES.keys()),
        key="selected_personality"
    )
    SYSTEM_INSTRUCTION = PERSONALITIES[selected_personality]

    if st.button("➕ New Chat", use_container_width=True):
        new_id = create_conversation()
        load_conversation(new_id)
        st.rerun()

    st.divider()

    # Export current conversation as a text file
    if st.session_state.messages:
        export_lines = []
        for msg in st.session_state.messages:
            speaker = "You" if msg["role"] == "user" else "Byte"
            export_lines.append(f"{speaker}: {msg['content']}")
        export_text = "\n\n".join(export_lines)

        st.download_button(
            label="Export chat (.txt)",
            data=export_text,
            file_name="chat_export.txt",
            mime="text/plain",
            use_container_width=True
        )

        def generate_pdf(messages):
            """Build a PDF transcript in memory and return its bytes."""
            buffer = BytesIO()
            doc = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter

            x_margin = 0.75 * inch
            y = height - 0.75 * inch
            line_height = 16

            doc.setFont("Helvetica-Bold", 14)
            doc.drawString(x_margin, y, "Chat Export - Byte")
            y -= line_height * 2

            doc.setFont("Helvetica", 11)
            for msg in messages:
                speaker = "You" if msg["role"] == "user" else "Byte"
                full_text = f"{speaker}: {msg['content']}"

                # First split on real newlines (paragraph breaks), THEN word-wrap each piece
                paragraphs = full_text.split("\n")
                wrapped_lines = []
                for paragraph in paragraphs:
                    if paragraph.strip() == "":
                        wrapped_lines.append("")  # preserve blank lines between paragraphs
                        continue
                    words = paragraph.split(" ")
                    current_line = ""
                    for word in words:
                        if len(current_line) + len(word) + 1 <= 90:
                            current_line += (word + " ")
                        else:
                            wrapped_lines.append(current_line)
                            current_line = word + " "
                    wrapped_lines.append(current_line)

                for line in wrapped_lines:
                    if y < 0.75 * inch:  # start a new page if we run out of room
                        doc.showPage()
                        doc.setFont("Helvetica", 11)
                        y = height - 0.75 * inch
                    doc.drawString(x_margin, y, line)
                    y -= line_height

                y -= line_height * 0.5  # extra spacing between messages

            doc.save()
            buffer.seek(0)
            return buffer

        pdf_buffer = generate_pdf(st.session_state.messages)
        st.download_button(
            label="Export chat (.pdf)",
            data=pdf_buffer,
            file_name="chat_export.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    # Track which conversation (if any) is currently being renamed
    if "editing_conv_id" not in st.session_state:
        st.session_state.editing_conv_id = None

    conversations = get_conversations()
    for conv in conversations:
        is_editing = st.session_state.editing_conv_id == conv["id"]

        if is_editing:
            # Show a text input + save/cancel buttons instead of the normal row
            new_title = st.text_input(
                "Rename chat",
                value=conv["title"],
                key=f"rename_input_{conv['id']}",
                label_visibility="collapsed"
            )
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Save", key=f"save_{conv['id']}", use_container_width=True):
                    rename_conversation(conv["id"], new_title.strip() or "Untitled")
                    st.session_state.editing_conv_id = None
                    st.rerun()
            with col2:
                if st.button("Cancel", key=f"cancel_{conv['id']}", use_container_width=True):
                    st.session_state.editing_conv_id = None
                    st.rerun()
        else:
            # Normal row: chat button, rename button, delete button
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                label = conv["title"]
                if conv["id"] == st.session_state.current_conversation_id:
                    label = f"**{label}**"
                if st.button(label, key=f"conv_{conv['id']}", use_container_width=True):
                    load_conversation(conv["id"])
                    st.rerun()
            with col2:
                if st.button("Edit", key=f"edit_{conv['id']}"):
                    st.session_state.editing_conv_id = conv["id"]
                    st.rerun()
            with col3:
                if st.button("X", key=f"del_{conv['id']}"):
                    delete_conversation(conv["id"])
                    if conv["id"] == st.session_state.current_conversation_id:
                        remaining = get_conversations()
                        if remaining:
                            load_conversation(remaining[0]["id"])
                        else:
                            load_conversation(create_conversation())
                    st.rerun()

# ---- MAIN CHAT AREA ----
st.title("🤖 Byte - Your Coding Mentor")

# Render the loaded conversation history in the main chat area.
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        copy_button(msg["content"], button_id=id(msg))

user_input = st.chat_input("Ask Byte something...")

if user_input:
    conv_id = st.session_state.current_conversation_id

    # Auto-title the conversation based on the first message
    if len(st.session_state.messages) == 0:
        title = user_input[:40] + ("..." if len(user_input) > 40 else "")
        rename_conversation(conv_id, title)

    st.session_state.messages.append({"role": "user", "content": user_input})
    save_message(conv_id, "user", user_input)
    with st.chat_message("user"):
        st.write(user_input)
        copy_button(user_input, button_id="new_user_msg")

    try:
        response = st.session_state.chat.send_message(user_input)
        bot_reply = response.text
    except Exception as e:
        bot_reply = f"Something went wrong: {e}"

    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    save_message(conv_id, "assistant", bot_reply)
    with st.chat_message("assistant"):
        st.write(bot_reply)
        copy_button(bot_reply, button_id="new_bot_reply")