import ngrok
import time

print("Starting ngrok tunnel...")

listener = ngrok.forward(
    5000,
    authtoken="3BhWAzBxAzAbnOYWWLXDAm2ICMi_7azpbp1RMV4DXhqCgaBWp"
)

print(f"Ngrok URL: {listener.url()}")
print("Tunnel is running... Do not close this terminal!")
print("Copy this URL and paste in Twilio Sandbox Settings + /whatsapp")

while True:
    time.sleep(10)