from flask import render_template, request, url_for, redirect, jsonify, session, flash
from create_app import create_app, mongo

app = create_app()
@app.route('/')
def home():
    if 'username' in session:
        users = mongo.db.users
        user = users.find_one({'name': session['username']})
        coin_count = user.get('coin_count', 0)
        account_balance = user.get('account_balance', 0)
        return render_template('home.html', coin_count=coin_count, account_balance=account_balance)
    else:
        return render_template('home.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        users = mongo.db.users
        existing_user = users.find_one({'name': request.form['username']})

        if existing_user is None:
            users.insert_one({'name': request.form['username'], 'password': request.form['password'], 'password_hint': request.form['password_hint']
                              ,'amount': 0, 'coin_count': 0})
            return jsonify({'success': True, 'redirect_url': url_for('home')})

        return jsonify({'success': False, 'error_msg': "이미 존재하는 사용자입니다."})

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = mongo.db.users
        login_user = users.find_one({'name': request.form['username']})
        if login_user :
            if request.form['password'] == login_user['password']:
                session['username'] = login_user['name']
                return jsonify({'success': True, 'redirect_url': url_for('home')})
            else:
                return jsonify({'success': False, 'error_msg': '로그인 실패! 아이디 또는 비밀번호가 잘못되었습니다.'})
        return jsonify({'success': False, 'error_msg': '회원가입 필요'})

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/search_password', methods=['GET', 'POST'])
def search_password():
    if request.method == 'POST':
        users = mongo.db.users
        existing_user = users.find_one({'name': request.form['username']})

        if existing_user is None:
            flash('사용자를 찾을 수 없습니다.')
            return redirect(url_for('search_password'))

        flash('비밀번호 힌트: ' + existing_user['password_hint'])
        return redirect(url_for('search_password'))

    return render_template('search_password.html')

@app.route('/deposit', methods=['POST'])
def deposit():
    if 'username' in session:
        amount = int(request.form['amount'])
        users = mongo.db.users
        user = users.find_one({'name': session['username']})
        current_amount = user.get('amount', 0)
        new_amount = current_amount + amount
        users.update_one({'name': session['username']}, {'$set': {'amount': new_amount}})
        return jsonify({'success': True})

if __name__ == '__main__':
    app.run()