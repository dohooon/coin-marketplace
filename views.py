from flask import render_template, request, url_for, redirect, jsonify, session, flash
from create_app import create_app, mongo
import pymongo
from datetime import datetime

app = create_app()

# 게시글 테이블
class TradePost:
    def __init__(self, user, coin_count, price, timestamp, status):
        self.user = user
        self.coin_count = coin_count
        self.price = price
        self.timestamp = timestamp
        self.status = status

    def save(self):
        # MongoDB에 게시글 저장
        trade_posts = mongo.db.trade_posts
        trade_posts.insert_one({
            'user': self.user,
            'coin_count': self.coin_count,
            'price': self.price,
            'timestamp': self.timestamp,
            'status': self.status
        })

def get_posts():
    trade_posts = mongo.db.trade_posts
    posts = trade_posts.find()
    post_list = []

    for post in posts:
        user = post['user']
        coin_count = post['coin_count']
        price = post['price']
        timestamp = post['timestamp']
        status = post['status']

        trade_post = TradePost(user=user, coin_count=coin_count, price=price, timestamp=timestamp, status=status)
        post_list.append(trade_post)

    return post_list


@app.route('/sell_coin', methods=['POST'])
def sell_coin():
    if 'username' in session:
        users = mongo.db.users
        marketplace = mongo.db.marketplace
        market_info = marketplace.find_one()

        sell_coin_count = int(request.json['sell_coin_count'])
        sell_coin_price = int(request.json['sell_coin_price'])

        user = users.find_one({'name': session['username']})
        user_coin_count = user.get('coin_count', 0)

        if sell_coin_count <= user_coin_count:
            new_user_coin_count = user_coin_count - sell_coin_count
            new_market_coin_count = market_info.get('coin_count', 0) + sell_coin_count

            #판매자가 게시글을 올리면 게시글에 올린 만큼의 코인이 마켓에 추가되고 판매자의 코인은 줄어듭니다.
            users.update_one({'name': session['username']}, {'$set': {'coin_count': new_user_coin_count}})
            marketplace.update_one({}, {'$set': {'coin_count': new_market_coin_count}})

            # 새로운 게시글 객체 생성
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            TradePost(user=session['username'], coin_count=sell_coin_count, price=sell_coin_price, timestamp=timestamp, status='판매 중').save()

            # 게시글 목록 가져오기
            posts = get_posts()

            return render_template('trade_post.html', posts=posts)
        else:
            return jsonify({'success': False, 'error_msg': "판매할 수 있는 코인 수량이 부족합니다."})

        return jsonify({'success': False, 'error_msg': "로그인이 필요합니다."})

@app.route('/trade_post', methods=['GET', 'POST'])
def trade_post():
    posts = get_posts()
    return render_template('trade_post.html', posts=posts)

def initialize_marketplace():
    marketplace = mongo.db.marketplace
    marketplace.insert_one({'coin_count': 100, 'coin_price': 100})

def add_coin_data(price):
    coin_data = mongo.db.coin_data
    timestamp = datetime.now()
    coin_data.insert_one({'price': price, 'timestamp': timestamp})

def update_marketplace(coin_count, coin_price):
    marketplace = mongo.db.marketplace
    marketplace.update_one({}, {'$set': {'coin_count': coin_count, 'coin_price': coin_price}})

with app.app_context():
    initialize_marketplace()

@app.route('/')
def home():
    marketplace = mongo.db.marketplace
    market_info = marketplace.find_one()

    # 코인 데이터 가져오기
    coin_data = mongo.db.coin_data.find({}, {"_id": 0, "timestamp": 1, "price": 1}).sort("timestamp", 1)
    coin_labels = []
    coin_prices = []

    # 시간대와 가격 데이터 추출 및 포맷팅
    for data in coin_data:
        timestamp = data["timestamp"]
        price = data["price"]

        formatted_timestamp = timestamp.strftime("%m월 %d일 %p %I시 %M분")
        coin_labels.append(formatted_timestamp)
        coin_prices.append(price)

    if 'username' in session:
        users = mongo.db.users
        user = users.find_one({'name': session['username']})
        coin_count = user.get('coin_count', 0)
        account_balance = user.get('account_balance', 0)
        return render_template('home.html', coin_count=coin_count, account_balance=account_balance, coin_labels=coin_labels, coin_prices=coin_prices, market_coin_count=market_info.get('coin_count', 0), market_coin_price=market_info.get('coin_price', 100))
    else:
        return render_template('home.html', coin_labels=coin_labels, coin_prices=coin_prices, market_coin_count=market_info.get('coin_count', 0), market_coin_price=market_info.get('coin_price', 100))
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

@app.route('/withdraw', methods=['POST'])
def withdraw():
    if 'username' in session:
        account_balance = int(request.form['account_balance'])
        users = mongo.db.users
        user = users.find_one({'name': session['username']})
        current_account_balance = user.get('account_balance', 0)
        new_account_balance = current_account_balance - account_balance
        if new_account_balance < 0 :
            return jsonify({'success': False, 'error_msg': '잔액이 부족합니다.'})
        users.update_one({'name': session['username']}, {'$set': {'account_balance': new_account_balance}})
        return jsonify({'success': True})

@app.route('/buy-coin', methods=['POST'])
def buy_coin():
    if 'username' in session:
        users = mongo.db.users
        marketplace = mongo.db.marketplace
        market_info = marketplace.find_one()

        # coin_price는 가장 최근 거래 가격을 따름
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

            # 코인 데이터 추가
            add_coin_data(coin_price)

            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error_msg': "구매할 수 있는 코인 수량 또는 계정 잔고가 부족합니다."})

    return jsonify({'success': False, 'error_msg': "로그인이 필요합니다."})

if __name__ == '__main__':
    app.run()
