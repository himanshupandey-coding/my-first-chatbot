import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("Error: GEMINI_API_KEY not found. Check your .env file.")
    exit()

client = genai.Client(api_key=api_key)

chat = client.chats.create(
    model="gemini-3.6-flash",
    config=types.GenerateContentConfig(
        system_instruction="You are a witty, slightly sarcastic coding mentor named Byte. Keep answers short and add a joke when it fits."
    )
)

print("Chatbot ready! Type 'exit' to quit.\n")

while True:
    try:
        user_input = input("You: ")

        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        if not user_input.strip():
            continue

        response = chat.send_message(user_input)
        print("Bot:", response.text)

    except KeyboardInterrupt:
        print("\nGoodbye!")
        break

    except Exception as e:
        print(f"Something went wrong: {e}")
        print("Try again.")