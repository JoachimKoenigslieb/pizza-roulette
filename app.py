from twilio.rest import Client
import random
from gtts import gTTS
import os
from dotenv import load_dotenv
from flask import Flask, send_file, request, render_template

load_dotenv()

app = Flask(__name__)

ACCOUNT_SID = os.getenv('ACCOUNT_SID')
AUTH_TOKEN = os.getenv('AUTH_TOKEN')
URL = os.getenv('URL')
FROM = os.getenv('FROM')

@app.route('/')
def index():
    return render_template('pizza_form.html')

@app.route('/call')
def call():
    name = request.args.get('name')
    number = request.args.get('number')
    low = request.args.get('low', 0)
    high = request.args.get('high', 50)
    pizzas = request.args.get('pizzas')

    print(f'{name} har bestil {pizzas} pizzaer imellem {low} og {high}. Han bestiller hos {number}')

    if not pizzas:
        return 'error! du skal vælge mindst en pizz', 404

    nonce = generate_speech(pizzas, low, high, name)

    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    
    resp = f"<Response><Play>{URL}/static/speech{nonce}.mp3</Play></Response>"
    call = client.calls.create(twiml=resp, to=f'+45{number}', from_=FROM)

    return f'jeg tror det virkede! Din nonce er {nonce}', 200

def generate_speech(n, low, high, name, debug=False): #generate speech that says: I would like to order one number {n}
    lst = [random.randint(int(low), int(high)) for _ in range(int(n))]    

    if len(lst) > 0:
        speech = f'Hej. Du snakker med {name}. Jeg er en robot. Jeg vil gerne bestille en nummer {"og en nummer".join([str(s) for s in n])}. Det var {"og en nummer".join([str(s) for s in n])}. Jeg henter om 20 minutter. Dette er ikke en prank. Mange tak.'
    else: 
        speech = f'Hej. Dette er et prank call. Jeg er ikke sulten'
   
    nonce = random.randint(0, 20000000)

    tts = gTTS(text=speech, lang='da')
    tts.save(f"./static/speech{nonce}.mp3")

    return nonce
