from twilio.rest import Client
import random
from gtts import gTTS
import os
from dotenv import load_dotenv
from flask import Flask, send_file, request, render_template
from flask_sockets import Sockets
import logging
import base64
import json

from twilio.twiml.voice_response import VoiceResponse, Start, Stream


load_dotenv()

app = Flask(__name__)
sockets = Sockets(app)

HTTP_SERVER_PORT = 5000
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
    
    resp = f"<Response><Play>https://{URL}/static/speech{nonce}.mp3</Play></Response>"
    call = client.calls.create(twiml=resp, to=f'+45{number}', from_=FROM)

    return f'jeg tror det virkede! Din nonce er {nonce}', 200

@app.route('/prank')
def prank():
    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    
    resp = f"""<?xml version="1.0" encoding="UTF-8"?><Response><Start><Stream url="wss://{URL}/stream"/></Start><Say>Hello, am i talking to joachim? I need to speak to him</Say></Response>"""
    call = client.calls.create(twiml=resp, from_=FROM, to='+4553370718')
    
    print(call)

    return 'went ok???', 200

@sockets.route('/stream')
def stream(ws):
    app.logger.info("Connection accepted")
    print('yo something goes here')
    # A lot of messages will be sent rapidly. We'll stop showing after the first one.
    has_seen_media = False
    message_count = 0
    while not ws.closed:
        message = ws.recieve()
        if message is None:
            app.logger.info('No message recieved...')
            continue
        
        data = json.loads(message)
        if data['event'] == "connected":
            app.logger.info("Connected Message received: {}".format(message))
        if data['event'] == "start":
            app.logger.info("Start Message received: {}".format(message))
        if data['event'] == "media":
            if not has_seen_media:
                app.logger.info("Media message: {}".format(message))
                payload = data['media']['payload']
                app.logger.info("Payload is: {}".format(payload))
                chunk = base64.b64decode(payload)
                app.logger.info("That's {} bytes".format(len(chunk)))
                app.logger.info("Additional media messages from WebSocket are being suppressed....")
                has_seen_media = True
        if data['event'] == "closed":
            app.logger.info("Closed Message received: {}".format(message))
            break
        message_count += 1

def generate_speech(n, low, high, name, debug=False): #generate speech that says: I would like to order one number {n}
    lst = [random.randint(int(low), int(high)) for _ in range(int(n))]    

    if len(lst) > 0:
        speech = f'Hej. Du snakker med {name}. Jeg er en robot. Jeg vil gerne bestille en nummer {"og en nummer".join([str(s) for s in lst])}. Det var {"og en nummer".join([str(s) for s in lst])}. Jeg henter om 20 minutter. Dette er ikke en prank. Mange tak.'
    else: 
        speech = f'Hej. Dette er et prank call. Jeg er ikke sulten'
   
    nonce = random.randint(0, 20000000)

    tts = gTTS(text=speech, lang='da')
    tts.save(f"./static/speech{nonce}.mp3")

    return nonce

if __name__ == '__main__':
    app.logger.setLevel(logging.DEBUG)
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    server = pywsgi.WSGIServer(('', HTTP_SERVER_PORT), app, handler_class=WebSocketHandler, log=app.logger)
    print("Server listening on: http://localhost:" + str(HTTP_SERVER_PORT))
    server.serve_forever()


