from flask import Flask, request, render_template
from groq import Groq
from twilio.twiml.messaging_response import MessagingResponse
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

my_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=my_key)




BOOKINGS_FILE = "bookings.json"
MENU_FILE = "menu.json"

def load_menu():
    with open(MENU_FILE, "r") as f:
        return json.load(f)

def load_bookings():
    if os.path.exists(BOOKINGS_FILE):
        with open(BOOKINGS_FILE, "r") as f:
            return json.load(f)
    return []

def save_booking(name, people, date, time):
    bookings = load_bookings()
    new_booking = {
        "id": len(bookings) + 1,
        "name": name,
        "people": people,
        "date": date,
        "time": time,
        "booked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    bookings.append(new_booking)
    with open(BOOKINGS_FILE, "w") as f:
        json.dump(bookings, f, indent=4)
    return new_booking["id"]

def build_system_prompt():
    data = load_menu()
    menu_text = ""
    for item in data["menu"]:
        menu_text += f"- {item['item']}: Rs. {item['price']}\n"
    prompt = f"""
You are a helpful assistant for {data['restaurant_name']}.

RESTAURANT INFO:
- Name: {data['restaurant_name']}
- Location: {data['location']}
- Opening Hours: {data['opening_hours']}
- Phone: {data['phone']}

MENU:
{menu_text}

BOOKING INSTRUCTIONS:
When customer gives name, people, date and time reply EXACTLY:
BOOKING_CONFIRMED|name|people|date|time

For all other questions reply normally.
Reply in same language as customer (Urdu or English)
"""
    return prompt

# Store conversations per phone number
conversations = {}

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    incoming_msg = request.values.get("Body", "").strip()
    sender = request.values.get("From", "")

    if sender not in conversations:
        conversations[sender] = []

    conversations[sender].append({
        "role": "user",
        "content": incoming_msg
    })

    response_text = ""

    chat = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": build_system_prompt()}
        ] + conversations[sender]
    )

    ai_response = chat.choices[0].message.content

    if ai_response.startswith("BOOKING_CONFIRMED"):
        parts = ai_response.split("|")
        booking_id = save_booking(parts[1], parts[2], parts[3], parts[4])
        response_text = f"""✅ Booking Confirmed!
Booking ID: #{booking_id}
Name: {parts[1]}
People: {parts[2]}
Date: {parts[3]}
Time: {parts[4]}
We look forward to seeing you!"""
    else:
        response_text = ai_response

    conversations[sender].append({
        "role": "assistant",
        "content": response_text
    })

    twilio_response = MessagingResponse()
    twilio_response.message(response_text)
    return str(twilio_response)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    session_id = data.get("session_id", "default")
    user_message = data.get("message", "")

    if session_id not in conversations:
        conversations[session_id] = []

    conversations[session_id].append({
        "role": "user",
        "content": user_message
    })

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": build_system_prompt()}
        ] + conversations[session_id]
    )

    ai_response = response.choices[0].message.content

    if ai_response.startswith("BOOKING_CONFIRMED"):
        parts = ai_response.split("|")
        booking_id = save_booking(parts[1], parts[2], parts[3], parts[4])
        ai_response = f"""✅ Booking Confirmed!
Booking ID: #{booking_id}
Name: {parts[1]}
People: {parts[2]}
Date: {parts[3]}
Time: {parts[4]}
We look forward to seeing you!"""

    conversations[session_id].append({
        "role": "assistant",
        "content": ai_response
    })

    return {"response": ai_response}

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, port=port, host='0.0.0.0')

