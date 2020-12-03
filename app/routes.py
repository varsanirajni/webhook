from app import app
from flask import make_response, request

import json
import requests

WEBHOOK_VERIFY_TOKEN = 'test_faq_token'
PAGE_ACCESS_TOKEN = 'EAAKPEy8kTZAIBANnG3Y6RnChQiU7cZC5ZBkqGJrtSQem2N1FbIfpFTfin68Jmu6csTEA0qCI8FaZAEEOqZB3mZA95KojIpfawBwPWlndz37tNvsTVzRuiZCLPQ7LSUlDI6OAJV23G0ie3D8ZAj5EZCUw1cpSlDyiTRZBfA3KPjPZAQtZBK4qhdpmqNxq'
#this is for page Page_thread_queue_test
PAGE_ACCESS_TOKEN2 = 'EAAC5xQUuOt8BAGm4ZBQd47MW1vzzM1WapiylCoGEPsEUojdUHMbPIrPeIi2i5S8ZAAahoVknfXPgJ4vlfJnuZBVijXzyZBS6QsHOPYrKtVhfQQLwoaQ1o1JpsZBgA4ZBZBeDs0WeZAe2uJv1xZAYNKEEKQreHnGM0JF8ZBu2vgK7F6RXtYTrcfSUFr'

SEND_API_URL = 'https://graph.facebook.com/v2.12/me/messages?access_token=%s'\
  % PAGE_ACCESS_TOKEN
SEND_API_URL2 = 'https://graph.facebook.com/v2.12/me/messages?access_token=%s'\
  % PAGE_ACCESS_TOKEN2

PASS_THREAD_CONTROL_URL = 'https://graph.facebook.com/v2.12/me/pass_thread_control?access_token=%s'\
  % PAGE_ACCESS_TOKEN

TAKE_THREAD_CONTROL_URL = 'https://graph.facebook.com/v2.12/me/take_thread_control?access_token=%s'\
% PAGE_ACCESS_TOKEN

HEADERS = {'content-type': 'application/json'}

PAGE_INBOX = 263902037430900

ME = '620697518375534'

def send_message(body):
  print('send_message')
  print(body)
  try:
    for entry in body['entry']:
        if 'messaging' in entry:
          channel = 'messaging'
        else:
          channel = 'standby'
        for message in entry[channel]:
          sender = message['sender']['id']
          recipient_id =  message['recipient']['id']
          
          if 'message' in message: 
            webhook_type='message'
          elif 'postback' in message:
            webhook_type='postback' 
          else:
            return
          if 'text' in message[webhook_type]:
            msg_text = message[webhook_type]['text']
            if 'echoing_back' in msg_text:
              return
          body['echoing_back'] = 'true'
          print('sender1111')
          if 'is_echo' in message[webhook_type]:
            send_message_to_recipient(json.dumps(body), recipient_id, sender)
          else:
            send_message_to_recipient(json.dumps(body), sender, recipient_id)
          print('sender')
          print(sender)
          return
    print('sender')
  except Exception as e:
     print("swapnilc-Exception sending")
     print(e)
      
      
def send_message_to_recipient(message_text, recipient_id, page_id):
  message = {
    'recipient': {
      'id': recipient_id,
    },
    'message': {
      'text': message_text,
    },
  }
  r = requests.post(SEND_API_URL if page_id == '620697518375534' else SEND_API_URL2, data=json.dumps(message), headers=HEADERS)
  if r.status_code != 200:
    print('== ERROR====')
    print(SEND_API_URL)
    print(r.json())
    print('==============')

def pass_thread_control(app_id, recipient_id):
  payload = {
    'recipient': {
      'id': recipient_id,
    },
    'target_app_id': app_id,
  }
  r = requests.post(PASS_THREAD_CONTROL_URL, data=json.dumps(payload), headers=HEADERS)
  if r.status_code != 200:
    print('====ERROR====')
    print(r.json())
    print(r.request.data)
    print('==============')

def take_thread_control(recipient_id):
  payload = {
    'recipient': {
      'id': recipient_id,
    },
  }
  r = requests.post(TAKE_THREAD_CONTROL_URL, data=json.dumps(payload), headers=HEADERS)
  if r.status_code != 200:
    print('====ERROR====')
    print(r.json())
    print(r.request.data)
    print('==============')

def pass_thread_control_to_page_inbox(recipient_id):
  pass_thread_control(PAGE_INBOX, recipient_id)

def handle_messaging_event(message):
  sender = message['sender']['id']
  if sender == ME:
    return

  if 'request_thread_control' in message:
    send_message_to_recipient('Transferring you to live agent.', sender)
    pass_thread_control(message['request_thread_control']['requested_owner_app_id'], sender)
    return

  if 'message' not in message:
    return
  if 'text' not in message['message']:
    return
  message_text = message['message']['text']
  if 'return policy' in message_text:
    send_message_to_recipient('We offer full refunds up to 30 days, with a valid receipt.', sender)
  elif 'address' in message_text:
    send_message_to_recipient('You can find us at 123 Hacker Way, Menlo Park, CA 94025.', sender)
  elif 'hours' in message_text:
    send_message_to_recipient('We\'re open 9:00 AM - 5:30 PM from Monday to Saturday.', sender)
  else:
    send_message_to_recipient('I\'m sorry, I am not able to help with that. I\'ll transfer you over to a live agent.', sender)
    pass_thread_control_to_page_inbox(sender)

def handle_standby_event(standby_event):
  if 'sender' not in standby_event:
    return
  if 'id' not in standby_event['sender']:
    return
  sender = standby_event['sender']['id']
  if 'message' not in standby_event:
    return
  if 'text' not in standby_event['message']:
    return
  message_text = standby_event['message']['text']
  if 'deliver' in message_text:
    take_thread_control(sender)
    send_message_to_recipient('I noticed you asking about delivery options. Let me redirect you to our automated delivery processing service.', sender)

def handle_entry(entry):
  if 'messaging' in entry:
    for message in entry['messaging']:
      handle_messaging_event(message)
  elif 'standby' in entry:
    for standby_event in entry['standby']:
      handle_standby_event(standby_event)

@app.route('/')
@app.route('/index')
def index():
  return 'Hello, World!'

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
  if request.method == 'GET':
    mode = request.args['hub.mode']
    token = request.args['hub.verify_token']
    challenge = request.args['hub.challenge']
    if mode and token:
      if mode == 'subscribe' and token == WEBHOOK_VERIFY_TOKEN:
        return challenge
      else:
        return make_response('wrong token', 403)
    else:
      return make_response('invalid params', 400)
  else: # POST
    body = json.loads(request.data)
    print("swapnilc-Mydata")
    print(body)
    send_message(body)
    return ("", 205)

