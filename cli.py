from groq import Groq
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

my_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=my_key)


BOOKINGS_FILE = "bookings.json"
MENU_FILE = "menu.json"


# Load menu from file
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


def view_all_bookings():
    bookings = load_bookings()

    if len(bookings) == 0:
        print("\n No bookings yet!")
        return

    print("\n")
    print("=" * 50)
    print("        LAHORE DHABBA — ALL BOOKINGS")
    print("=" * 50)

    for booking in bookings:
        print(f"""
Booking ID : #{booking['id']}
Name       : {booking['name']}
People     : {booking['people']}
Date       : {booking['date']}
Time       : {booking['time']}
Booked At  : {booking['booked_at']}
{'-' * 50}""")

    print(f"TOTAL BOOKINGS: {len(bookings)}")
    print("=" * 50)


# Build system prompt from menu file
def build_system_prompt():
    data = load_menu()

    menu_text = ""
    for item in data["menu"]:
        menu_text += f"- {item['item']}: Rs. {item['price']}\n"

    prompt = f"""
You are a helpful assistant for a restaurant called "{data['restaurant_name']}".

RESTAURANT INFO:
- Name: {data['restaurant_name']}
- Location: {data['location']}
- Opening Hours: {data['opening_hours']}
- Phone: {data['phone']}

MENU:
{menu_text}
BOOKING INFO:
- Table booking available
- Maximum {data['booking_rules']['max_people']} people per booking
- Advance booking required for groups of {data['booking_rules']['advance_required_for']} or more

IMPORTANT BOOKING INSTRUCTIONS:
When a customer wants to book a table and gives you:
- Their name
- Number of people
- Date
- Time

You must reply with EXACTLY this format and nothing else:
BOOKING_CONFIRMED|name|people|date|time

Example:
BOOKING_CONFIRMED|Abdullah|4|2026-03-30|7pm

For all other questions reply normally.
Reply in the same language the customer uses (Urdu or English)
"""
    return prompt


conversation_history = []

# Load menu once at start
system_prompt = build_system_prompt()
menu_data = load_menu()

print("=" * 50)
print(f"   {menu_data['restaurant_name']} AI ASSISTANT")
print("=" * 50)
print("Type your question and press Enter")
print("Type 'exit' to quit")
print("Type 'owner' to view all bookings")
print("=" * 50)

while True:
    user_input = input("Customer: ")

    if user_input.lower() == "exit":
        print(f"Thank you for contacting {menu_data['restaurant_name']}!")
        break

    if user_input.lower() == "owner":
        view_all_bookings()
        continue

    conversation_history.append({
        "role": "user",
        "content": user_input
    })

    chat = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
                     {"role": "system", "content": system_prompt}
                 ] + conversation_history
    )

    response = chat.choices[0].message.content

    if response.startswith("BOOKING_CONFIRMED"):
        parts = response.split("|")
        name = parts[1]
        people = parts[2]
        date = parts[3]
        time = parts[4]

        booking_id = save_booking(name, people, date, time)

        confirmation = f"""
✅ Booking Confirmed!
━━━━━━━━━━━━━━━━━━━━
Booking ID : #{booking_id}
Name       : {name}
People     : {people}
Date       : {date}
Time       : {time}
━━━━━━━━━━━━━━━━━━━━
We look forward to seeing you!
        """
        print(f"{menu_data['restaurant_name']} Assistant: {confirmation}")

        conversation_history.append({
            "role": "assistant",
            "content": confirmation
        })

    else:
        print(f"{menu_data['restaurant_name']} Assistant: {response}")
        conversation_history.append({
            "role": "assistant",
            "content": response
        })

    print("-" * 50)