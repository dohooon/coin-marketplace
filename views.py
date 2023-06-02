from flask import render_template, request, url_for, redirect, jsonify, session, flash
from create_app import create_app, mongo

app = create_app()

def initialize_marketplace():
    marketplace = mongo.db.marketplace
    marketplace.insert_one({'coin_count': 100, 'coin_price': 100})

with app.app_context():
    initialize_marketplace()

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
                              ,'account_balance': 0, 'coin_count': 0})
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
        account_balance = int(request.form['account_balance'])
        users = mongo.db.users
        user = users.find_one({'name': session['username']})
        current_account_balance = user.get('account_balance', 0)
        new_account_balance = current_account_balance + account_balance
        users.update_one({'name': session['username']}, {'$set': {'account_balance': new_account_balance}})
        return jsonify({'success': True})
@app.route('/buy-coin', methods=['POST'])
def buy_coin():
    if 'username' in session:
        users = mongo.db.users
        marketplace = mongo.db.marketplace
        market_info = marketplace.find_one()

        coin_price = market_info.get('coin_price', 100)
        coin_count = int(request.form['coin_count'])

        user = users.find_one({'name': session['username']})
        account_balance = user.get('account_balance', 0)

        if coin_count <= market_info.get('coin_count', 0) and coin_price * coin_count <= account_balance:
            new_balance = account_balance - coin_price * coin_count
            new_market_coin_count = market_info.get('coin_count', 0) - coin_count
            new_user_coin_count = user.get('coin_count', 0) + coin_count

            users.update_one({'name': session['username']}, {'$set': {'account_balance': new_balance, 'coin_count': new_user_coin_count}})
            marketplace.update_one({}, {'$set': {'coin_count': new_market_coin_count}})

            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error_msg': "구매할 수 있는 코인 수량 또는 계정 잔고가 부족합니다."})

    return jsonify({'success': False, 'error_msg': "로그인이 필요합니다."})

if __name__ == '__main__':
    app.run()