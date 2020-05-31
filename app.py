import os

import boto3

from flask import Flask, request, jsonify
app = Flask(__name__)

EXPENSES_TABLE = os.environ['EXPENSES_TABLE']
client = boto3.client('dynamodb')

@app.route('/')
def home():
    return 'Hello homepage!'

@app.route('/hello/<name>')
def hello(name):
    return 'Hello ' + name + '!'

@app.route('/expenses/<string:user_id>', methods=['GET'])
def get_user_expenses(user_id):
    resp = client.get_item(
        TableName = EXPENSES_TABLE,
        Key = {
            'userId': { 'S': user_id }
        }
    )
    item = resp.get('Item')
    if not item:
        return jsonify({ 'error': 'User does not exist' }), 404
    return jsonify({
        'userId': item.get('userId').get('N'),
        'category': item.get('category').get('S'),
        'amount': item.get('amount').get('N')
    })

@app.route('/expenses', methods=['POST'])
def create_expense():
    user_id = request.json.get('userId')
    category = request.json.get('category')
    amount = request.json.get('amount')
    if not user_id or not category or not amount:
        return jsonify({ 'error': 'Please provide userId, category, and amount' }), 400
    
    resp = client.put_item(
        TableName = EXPENSES_TABLE,
        Item = {
            'userId': { 'N': user_id },
            'category': { 'S': category },
            'amount': { 'N': amount }
        }
    )

    return jsonify({
        'userId': user_id,
        'category': category,
        'amount': amount
    })
