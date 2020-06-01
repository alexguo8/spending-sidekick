import os
import boto3
from flask import Flask, request, jsonify, Response
import requests
import json
app = Flask(__name__)

verify_token = os.environ['VERIFY_TOKEN']
access_token = os.environ['ACCESS_TOKEN']
dialogflow_access_token = os.environ['DIALOGFLOW_ACCESS_TOKEN']
dialogflow_project_id = os.environ['DIALOGFLOW_PROJECT_ID']
EXPENSES_TABLE = os.environ['EXPENSES_TABLE']
client = boto3.client('dynamodb')

@app.route('/')
def home():
    return 'Hello! I am a bot.'

@app.route('/webhook', methods=['GET'])
def webhook_verify():
    if request.args.get('hub.verify_token') == verify_token:
        return request.args.get('hub.challenge')
    return 'Invalid Verify Token'

@app.route('/webhook', methods=['POST'])
def webhook_post():
    data = json.loads(request.data.decode('utf-8'))
    for entry in data['entry']:
        user_message = entry['messaging'][0]['message']['text']
        user_id = entry['messaging'][0]['sender']['id']
        response = {
            'recipient': {'id': user_id},
            'message': {}
        }
        response['message']['text'] = respond_message(user_id, user_message)
        r = requests.post(
            'https://graph.facebook.com/v2.6/me/messages/?access_token=' + access_token, json=response)
    return Response(response="EVENT RECEIVED", status=200)

def respond_message(user_id, user_message):
    if 'get' in user_message or 'view' in user_message:
        return get_user_expenses(user_id)
    query = {
        "queryInput": {
            "text": {
                "languageCode": "en-CA",
                "text": user_message
            }
        }
    }
    headers = {
        'Authorization': 'Bearer ' + dialogflow_access_token,
        'ContentType': 'application/json'
    }
    res = requests.post(
        'https://dialogflow.googleapis.com/v2/projects/' + dialogflow_project_id + '/agent/sessions/3:detectIntent', headers=headers, json=query)
    response_json = res.json()
    if response_json['queryResult']['parameters']['Category']:
        category = response_json['queryResult']['parameters']['Category']
    if response_json['queryResult']['unit-currency'] and response_json['queryResult']['unit-currency']['amount']:
        amount = str(response_json['queryResult']['parameters']['unit-currency']['amount'])
    if not category or not amount:
        return 'Unable to recognize a category and/or amount.'
    return create_expense(user_id, category, amount)

def get_user_expenses(user_id):
    response = client.get_item(
        TableName=EXPENSES_TABLE,
        Key={
            'userId': { 'S': user_id }
        }
    )
    item = response.get('Item')
    if not item:
        return 'You do not have any previous expenses.'
    return 'Your last expense was for ' + item.get('categoru').get('S') + \
        ' costing ' + item.get('amount').get('N') + '.'

def create_expense(user_id, category, amount):
    response = client.put_item(
        TableName = EXPENSES_TABLE,
        Item = {
            'userId': { 'N': user_id },
            'category': { 'S': category },
            'amount': { 'N': amount }
        }
    )

    return 'Added expense of ' + amount + ' for ' + category + '.'