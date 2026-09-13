# 🤖 Byte - AI Chatbot

A personal AI chatbot built with Google's Gemini API, featuring persistent conversation history, multiple chat threads, selectable personalities, and chat export — built as a learning project to understand how modern AI-powered applications work end to end.

## Live Demo

[my-first-chatbot-x.streamlit.app](https://my-first-chatbot-x.streamlit.app)

## Features

- **AI-powered conversations** using Google's Gemini API
- **Multiple chat threads** — create, switch between, rename, and delete conversations
- **Persistent history** — conversations are saved in a SQLite database and survive restarts
- **Selectable personalities** — choose Byte's tone (Sarcastic Mentor, Strict Professor, Chill Friend, Motivational Coach)
- **Export conversations** as `.txt` or `.pdf`
- **Copy-to-clipboard** on any message
- **Clean error handling** for API/network issues

## Tech Stack

- **Python** — core application logic
- **Streamlit** — web interface
- **Google Gemini API** (`google-genai`) — AI responses
- **SQLite** — persistent storage
- **ReportLab** — PDF generation
- **python-dotenv** — secure API key management

## Running Locally

1. Clone this repository:
```bash
   git clone https://github.com/himanshupandey-coding/my-first-chatbot.git
   cd my-first-chatbot
```

2. Create and activate a virtual environment:
```bash
   python -m venv venv
   venv\Scripts\activate   # Windows
```

3. Install dependencies:
```bash
   pip install -r requirements.txt
```

4. Create a `.env` file in the project root with your Gemini API key: 

GEMINI_API_KEY=your_key_here

   Get a free key at [Google AI Studio](https://aistudio.google.com/).

5. Run the app:
```bash
   streamlit run app.py
```

## Project Structure
├── app.py # Streamlit web app (main entry point)
├── chatbot.py # Terminal version of the chatbot
├── database.py # SQLite database logic (conversations & messages)
├── requirements.txt # Python dependencies
└── .gitignore

## What I Learned

Building this project taught me:
- Working with Python virtual environments and dependency management
- Securely handling API keys with environment variables
- Calling an LLM API and understanding stateless conversation history
- SQL fundamentals — tables, foreign keys, CRUD operations
- Streamlit's execution model (`session_state`, reruns)
- Git and GitHub fundamentals
- Real-world debugging: dependency conflicts, deprecated APIs, browser security constraints

## Author
Himanshu Pandey

