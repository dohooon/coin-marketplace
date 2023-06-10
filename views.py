from flask import render_template, request, url_for, redirect, jsonify, session, flash
from create_app import create_app, mongo
from bson.objectid import ObjectId
from datetime import datetime
from flask import Flask
from flask_pymongo import PyMongo

app = create_app()


class TradePost:
    def __init__(self, _id, user, coin_count, price, timestamp, status):
        self._id = _id
        self.user = user
        self.coin_count = coin_count
        self.price = price
        self.timestamp = timestamp
        self.status = status

    def save(self):

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
        _id = post['_id']
        user = post['user']
        coin_count = post['coin_count']
        price = post['price']
        timestamp = post['timestamp']
        status = post['status']

        trade_post = TradePost(_id=_id, user=user, coin_count=coin_count, price=price, timestamp=timestamp, status=status)
        post_list.append(trade_post)

    post_list.sort(key=lambda x: x.timestamp, reverse=True)
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


            users.update_one({'name': session['username']}, {'$set': {'coin_count': new_user_coin_count}})
            marketplace.update_one({}, {'$set': {'coin_count': new_market_coin_count}})


            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            TradePost(_id=ObjectId(), user=session['username'], coin_count=sell_coin_count, price=sell_coin_price, timestamp=timestamp, status='판매 중').save()


            posts = get_posts()

            return render_template('trade_post.html', posts=posts)
        else:
            return jsonify({'success': False, 'error_msg': "판매할 수 있는 코인 수량이 부족합니다."})

        return jsonify({'success': False, 'error_msg': "로그인이 필요합니다."})


@app.route('/delete_post/<post_id>', methods=['POST'])
def delete_post(post_id):
    if 'username' in session:
        trade_posts = mongo.db.trade_posts
        users = mongo.db.users
        marketplace = mongo.db.marketplace
        market_info = marketplace.find_one()

        post = trade_posts.find_one({"_id": ObjectId(post_id)})
        if post and post['user'] == session['username']:
            post_coin_count = post.get('coin_count', 0)
            user = users.find_one({'name': session['username']})
            user_coin_count = user.get('coin_count', 0)


            new_user_coin_count = user_coin_count + post_coin_count
            new_market_coin_count = market_info.get('coin_count', 0) - post_coin_count

            users.update_one({'name': session['username']}, {'$set': {'coin_count': new_user_coin_count}})
            marketplace.update_one({}, {'$set': {'coin_count': new_market_coin_count}})


            trade_posts.delete_one({"_id": ObjectId(post_id)})
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error_msg': "이 게시글을 삭제할 권한이 없습니다."})
    else:
        return jsonify({'success': False, 'error_msg': "로그인이 필요합니다."})

@app.route('/buy_coin_from_post/<post_id>', methods=['POST'])
def buy_coin_from_post(post_id):
    if 'username' in session:
        trade_posts = mongo.db.trade_posts
        users = mongo.db.users
        marketplace = mongo.db.marketplace
        market_info = marketplace.find_one()

        post = trade_posts.find_one({"_id": ObjectId(post_id)})
        if post:
            buy_count = int(request.json['buyCount'])
            post_user = post['user']
            post_coin_count = post['coin_count']
            post_coin_price = post['price']
            post_user_balance = users.find_one({'name': post_user}).get('account_balance', 0)
            buyer = users.find_one({'name': session['username']})
            buyer_balance = buyer.get('account_balance', 0)
            buyer_coin_count = buyer.get('coin_count', 0)

            if buy_count <= post_coin_count and buy_count * post_coin_price <= buyer_balance:
                new_post_coin_count = post_coin_count - buy_count
                new_post_user_balance = post_user_balance + buy_count * post_coin_price
                new_buyer_balance = buyer_balance - buy_count * post_coin_price
                new_buyer_coin_count = buyer_coin_count + buy_count


                new_market_coin_count = market_info.get('coin_count', 0) - buy_count
                marketplace.update_one({}, {'$set': {'coin_count': new_market_coin_count}})
                marketplace.update_one({}, {'$set': {'coin_price': post_coin_price}})


                users.update_one({'name': post_user}, {'$set': {'account_balance': new_post_user_balance}})
                users.update_one({'name': session['username']}, {'$set': {'account_balance': new_buyer_balance, 'coin_count': new_buyer_coin_count}})


                add_coin_data(post_coin_price)

                trade_posts.update_one({"_id": ObjectId(post_id)}, {'$set': {'coin_count': new_post_coin_count}})
                if new_post_coin_count == 0:
                    trade_posts.update_one({"_id": ObjectId(post_id)}, {'$set': {'status': '거래 완료'}})

                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error_msg': "구매할 수 있는 코인 수량 또는 계정 잔고가 부족합니다."})
        else:
            return jsonify({'success': False, 'error_msg': "게시글을 찾을 수 없습니다."})

    return jsonify({'success': False, 'error_msg': "로그인이 필요합니다."})

@app.route('/trade_post', methods=['GET', 'POST'])
def trade_post():
    posts = get_posts()
    if posts is None:
        posts = []
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


    coin_data_db = mongo.db.coin_data
    coin_data = coin_data_db.find({}, {"_id": 0, "timestamp": 1, "price": 1}).sort("timestamp", 1)
    coin_labels = []
    coin_prices = []


    last_two_prices = list(coin_data_db.find().sort([('timestamp', -1)]).limit(2))

    if len(last_two_prices) < 2:

        coin_change_rate = 0
    else:

        coin_change_rate = round(
            ((last_two_prices[0]['price'] - last_two_prices[1]['price']) / last_two_prices[1]['price']) * 100, 2)


    prev_date = None
    for data in coin_data:
        timestamp = data["timestamp"]
        price = data["price"]

        formatted_timestamp = timestamp.strftime("%m/%d %I:%M%p")

        if prev_date == timestamp.date():
            formatted_timestamp = timestamp.strftime("%I:%M%p")
        else:
            prev_date = timestamp.date()

        coin_labels.append(formatted_timestamp)
        coin_prices.append(price)

    if 'username' in session:
        users = mongo.db.users
        user = users.find_one({'name': session['username']})
        coin_count = user.get('coin_count', 0)
        account_balance = user.get('account_balance', 0)
        return render_template('home.html', coin_change_rate=coin_change_rate, coin_count=coin_count,
                               account_balance=account_balance, coin_labels=coin_labels, coin_prices=coin_prices,
                               market_coin_count=market_info.get('coin_count', 0),
                               market_coin_price=market_info.get('coin_price', 100))
    else:
        return render_template('home.html', coin_change_rate=coin_change_rate, coin_labels=coin_labels,
                               coin_prices=coin_prices, market_coin_count=market_info.get('coin_count', 0),
                               market_coin_price=market_info.get('coin_price', 100))


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

            add_coin_data(coin_price)

            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error_msg': "구매할 수 있는 코인 수량 또는 계정 잔고가 부족합니다."})

    return jsonify({'success': False, 'error_msg': "로그인이 필요합니다."})


if __name__ == '__main__':
    app.run()

