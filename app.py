import os.path
import re
import sqlite3

from datetime import timedelta, datetime
from typing import Counter
from flask import Flask, jsonify, make_response, redirect, render_template, request, session, url_for, request
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = 'Flask%Crud#Application'

app.permanent_session_lifetime = timedelta(minutes=10)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "db.sqlite")

conn = sqlite3.connect(db_path, check_same_thread=False)

cursor_setup = conn.cursor()
cursor_setup.execute('CREATE TABLE IF NOT EXISTS users(username text, email text, password text)')
conn.commit()
cursor_setup.execute('CREATE TABLE IF NOT EXISTS tasks(username text, date text, task text)')
conn.commit()
cursor_setup.execute('CREATE TABLE IF NOT EXISTS completedTasks(username text, date text, task text)')
conn.commit()
cursor_setup.execute('CREATE TABLE IF NOT EXISTS points(username text, points int)')
conn.commit()
cursor_setup.close()

Counter = 0

@app.route('/')
def welcome():
    return render_template("welcome.html")

@app.route('/store')
def store():
    if 'loggedin' in session:
        return render_template("store.html")
    return render_template("login.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ''

    if request.method == 'POST' and 'userz' in request.form and 'passwordz' in request.form:
        session.permanent = True

        username = request.form['userz']
        password = request.form['passwordz']

        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))

        user = cursor.fetchone()

        if user and check_password_hash(user[2], password):
            session['loggedin'] = True
            session['username'] = user[0]

            return redirect(url_for('home'))
        else:
            message = 'Incorrect username/password'

    if request.method == 'POST' and 'username' in request.form and 'email' in request.form and 'password' in request.form:

        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hash = generate_password_hash(password)

        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))  
        user = cursor.fetchone()

        if user:
            message = 'Username/user already exists!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            message = 'Username must contain only characters and numbers!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            message = 'Invalid email address!'
        elif not username or not password or not email:
            message = 'Please fill out the form!'
        else:
            cursor.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                           (username, email, hash,))
            conn.commit()
            message = 'You have successfully registered!'
            return render_template('login.html')

    elif request.method == "POST":
        message = 'Please fill all required fields!'
    
    return render_template("login.html", message=message)

@app.route('/home', methods=['POST', 'GET'])
def home():

    if 'loggedin' in session:

        dateandtime = datetime.now()
        rightNow = dateandtime.hour + ( dateandtime.minute/60 )
        status = ( (24 - rightNow) / 24 ) * 100
        day = get_date()
        cursor = conn.cursor()
        cursor.execute( 'SELECT * FROM completedTasks WHERE username = ? and date = ?', (session['username'], day,))
        vari = cursor.fetchall()
        vari = len(vari)
        vari = vari * 10
        status = vari + status
        status = int(status)
        msg = ""
        global Counter

        if status >= 100:
            status = 100
            if Counter == 0:
                msg = "You get 200 points!"
                Counter += 1
                cursor.execute('INSERT INTO points ( username, points ) VALUES (?, ?)', (session['username'], 200)) 
                conn.commit() 
        else:
            Counter = 0
        
        if status < 20:
            image = url_for('static',filename ='murg_orange_hurt.png')
        elif status < 40:
            image = url_for('static',filename ='murg_orange.png')
        elif status < 50:
            image = url_for('static',filename ='murg_blue_teal_hurt.png')
        elif status < 70:
            image = url_for('static',filename ='murg_blue.png')
        elif status < 90:
            image = url_for('static',filename ='murg_spikey_hurt.png')
        else:
            image = url_for('static',filename ='murg_spikey_green.png')

        return render_template("index.html", username=session['username'], status=status, image=image, message=msg)
        
    return render_template("login.html")

@app.route('/myaccount')
def myaccount():
    if 'loggedin' in session:

        day = get_date()
        cursor = conn.cursor()
        cursor.execute( 'SELECT task FROM completedTasks WHERE username = ? and date = ?', (session['username'], day,))
        tasks = cursor.fetchall()
        cursor.execute( 'SELECT points FROM points WHERE username = ?', (session['username'],))
        points = cursor.fetchall()
        pointsTotal = 0
        for i in points:
            pointsTotal += i[0]

        eggs=[url_for('static',filename ='egg1.png'), url_for('static',filename ='egg2.png'), 
        url_for('static',filename ='egg3.png'), url_for('static',filename ='egg4.png'), 
        url_for('static',filename ='egg5.png'), url_for('static',filename ='egg6.png'), 
        url_for('static',filename ='egg7.png'), url_for('static',filename ='egg8.png'), 
        url_for('static',filename ='egg9.png'), url_for('static',filename ='egg10.png')]

        return render_template("myaccount.html", eggs=eggs, tasks=tasks, points=pointsTotal)

    return render_template("login.html")

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('username', None)
    return redirect(url_for('welcome'))

@app.route('/reset')
def reset():
    if session['username'] == "benprentice":
        cursor = conn.cursor()
        cursor.execute ('DROP TABLE IF EXISTS tasks')
        conn.commit()
        cursor.execute('CREATE TABLE tasks(username text, date text, task text)')
        conn.commit()
        cursor.execute ('DROP TABLE IF EXISTS completedTasks')
        conn.commit()
        cursor.execute('CREATE TABLE completedTasks(username text, date text, task text)')
        conn.commit()
        return render_template("404.html")

@app.errorhandler(404)  
def not_found(e):
    return render_template("404.html")

@app.route('/task_added', methods = ['POST'])
def task_added():
    if request.method == "POST":
        jsonData = request.get_json()
        day = get_date()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO tasks ( username, date, task ) VALUES (?, ?, ?)', 
            (session['username'], day, jsonData["task"],))
        conn.commit()
        return {
            'response' : 'I am the response'
        }

@app.route('/task_completed', methods = ['POST'])
def task_completed():
    if request.method == "POST":
        jsonData = request.get_json()
        day = get_date()
        cursor = conn.cursor()
        cursor.execute('SELECT task FROM completedTasks WHERE username = ? AND task = ?', (session['username'], jsonData["task"],)) 
        task = cursor.fetchone()
        if task is None:
            cursor.execute('INSERT INTO completedTasks ( username, date, task ) VALUES (?, ?, ?)', 
                (session['username'], day, jsonData["task"],))
            conn.commit()
        else:
            cursor.execute('DELETE FROM completedTasks WHERE username = ? and task = ?', (session['username'], jsonData["task"],)) 
            conn.commit()
        return {
            'response' : 'I am the response'
        }

@app.route('/task_load_to_js', methods = ['GET'])
def task_load_to_js():
    if request.method == "GET":
        day = get_date()
        cursor = conn.cursor()
        cursor.execute('SELECT task FROM tasks WHERE username = ? and date = ?', (session['username'], day,)) 
        tasks = cursor.fetchall()
        cursor.execute('SELECT task FROM completedTasks WHERE username = ? and date = ?', (session['username'], day,))
        two = cursor.fetchall()
        # find tasks that are checked off
        checked_tasks = []
        for i in tasks:
            if i in two:
                checked_tasks.append(i[0])
        tasks = jsonify({ 'tasks' : tasks,
                          'check' : checked_tasks })
        return tasks

@app.route('/task_deleted', methods = ['POST'])
def task_deleted():
    if request.method == "POST":
        jsonData = request.get_json()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM tasks WHERE username = ? and task = ?', (session['username'], jsonData["task"],)) 
        conn.commit()
        return {
            'response' : 'I am the response'
        }

def get_date():
    dateandtime = datetime.now()
    day = dateandtime.day
    month = dateandtime.month
    year = dateandtime.year
    day = str(month) + "-" + str(day) + "-" + str(year)
    return day

if __name__ == "__main__":
    app.run()