from flask import Flask, render_template, request, url_for, redirect
from flask_pymongo import PyMongo

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/myDatabase"  # 여기에 실제 데이터베이스 URI를 입력
mongo = PyMongo(app)


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        users = mongo.db.users
        existing_user = users.find_one({'name': request.form['username']})

        if existing_user is None:
            users.insert({'name': request.form['username'], 'password': request.form['password']})
            return redirect(url_for('home'))

        return '이미 존재하는 사용자입니다.'

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = mongo.db.users
        login_user = users.find_one({'name': request.form['username']})

        if login_user:
            if request.form['password'] == login_user['password']:
                return redirect(url_for('home'))

        return '로그인 실패! 아이디 또는 비밀번호가 잘못되었습니다.'

    return render_template('login.html')
