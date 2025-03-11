# save this as app.py
from flask import Flask, request
from markupsafe import escape
import requests as rq

app = Flask(__name__)

def handle_get():
    return 'me has mandado un GET'
def handle_post():
    data= request.form
    username = data.get('username')
    password = data.get('password')
    return f'me has mandado un POST con {username} y {password}'


@app.route('/')
def index():
    return 'Hola mundo'


@app.route('/test_get/<message>',methods=['GET'])
def test_get(message):
    return f'Hola {escape(message)}'


@app.route('/test_post', methods=['POST'])
def test_post():
    output_string = ""
    for key, value in request.form.items():
        output_string += f"{key}: {value}\n"  
    return 'me has mandado un POST con \n' + output_string


@app.route('/test_get_post', methods=['GET', 'POST'])
def test_get_post():
    if request.method == 'POST':
        return handle_post()
    else:
        return handle_get()

if __name__ == '__main__':
    app.run(host= '192.168.1.157', debug=True, port=8000)
    