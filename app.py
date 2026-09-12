import os
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
from database import (
    init_db, create_conversation, get_conversations,
    rename_conversation, save_message, load_messages, delete_conversation
)

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

init_db()

st.set_page_config(page_title="Byte - AI Chatbot", page_icon="🤖")

if not api_key:
    st.error("GEMINI_API_KEY not found. Check your .env file.")
    st.stop()

SYSTEM_INSTRUCTION = "You are a witty, slightly sarcastic coding mentor named Byte. Keep answers short and add a joke when it fits."

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

    st.session_state.chat = st.session_state.client.chats.create(
        model="gemini-3.6-flash",
        history=formatted_history,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
    )
    st.session_state.messages = messages

# Build the active chat session if we haven't yet (first run, or after switching conversations)
if "chat" not in st.session_state:
    load_conversation(st.session_state.current_conversation_id)

# ---- SIDEBAR ----
with st.sidebar:
    st.header("💬 Conversations")

    if st.button("➕ New Chat", use_container_width=True):
        new_id = create_conversation()
        load_conversation(new_id)
        st.rerun()

    st.divider()

    conversations = get_conversations()
    for conv in conversations:
        col1, col2 = st.columns([3, 1])
        with col1:
            label = conv["title"]
            if conv["id"] == st.session_state.current_conversation_id:
                label = f"**{label}**"  # bold the active one
            if st.button(label, key=f"conv_{conv['id']}", use_container_width=True):
                load_conversation(conv["id"])
                st.rerun()
        with col2:
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

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

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

    try:
        response = st.session_state.chat.send_message(user_input)
        bot_reply = response.text
    except Exception as e:
        bot_reply = f"Something went wrong: {e}"

    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    save_message(conv_id, "assistant", bot_reply)
    with st.chat_message("assistant"):
        st.write(bot_reply)