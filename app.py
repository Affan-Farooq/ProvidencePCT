import html
import json
import requests
from cs50 import SQL
import urllib.request
from flask_session import Session
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from ancillary import login_required, percent, usd, intFormat, usdTrad, monetaryChange

app = Flask(__name__)

app.jinja_env.filters["percent"] = percent
app.jinja_env.filters["usd"] = usd
app.jinja_env.filters["intFormat"] = intFormat
app.jinja_env.filters["usdTrad"] = usdTrad
app.jinja_env.filters["monetaryChange"] = monetaryChange

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

newsApiKey = "802af34e6a8289ab90b6e5eecd705aa7"
newsUrl = f"https://gnews.io/api/v4/search?q=crypto&lang=en&country=us&max=24&apikey={newsApiKey}"

db = SQL("sqlite:///project.db")

url_1 = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
url_2 = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/ohlcv/latest"
url_3 = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/ohlcv/historical'

headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': 'af84bb7c-07f9-4f67-835b-c837dbedb697',
}


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    userInfo = db.execute("SELECT * FROM users WHERE id = ?", session["userID"])
    userFinancialInfo = db.execute("SELECT * FROM holdings WHERE id = ?", session["userID"])
    if userFinancialInfo == []:

        dataEmpty = {
            "name": userInfo[0]["name"],
            "cash": userInfo[0]["cash"],
            "account_value": userInfo[0]["cash"],
            "percent_performance": ((userInfo[0]["cash"] / 100000) - 1) * 100,
            "monetary_performance": userInfo[0]["cash"] - 100000
        }

        return render_template("index2.html", data=dataEmpty)

    else:

        data = {
            "name": userInfo[0]["name"],
            "cash": userInfo[0]["cash"],
            "portfolio_value": 0,
            "account_value": 0,
            "assets": [],
            "asset_value": [],
            "percent_performance": 0,
            "monetary_performance": 0,
            "tabular_data": []
        }

        tickerList = []
        tickerList2 = ['CASH']
        polarData = [userInfo[0]["cash"]]
        for holding in userFinancialInfo:
            data["assets"].append(holding["ticker"])

            parameters = {
                'symbol': holding["ticker"],
                'convert': 'USD'
            }

            response = requests.get(url_1, headers=headers, params=parameters)
            assetData = response.json()

            holdingData = {
                "name": assetData["data"][holding["ticker"]]["name"],
                "ticker": holding["ticker"],
                "shares": holding["shares"],
                "pc": assetData["data"][holding["ticker"]]["quote"]["USD"]["percent_change_24h"],
                "price": assetData["data"][holding["ticker"]]["quote"]["USD"]["price"],
                "total": assetData["data"][holding["ticker"]]["quote"]["USD"]["price"] * holding["shares"],
                "id": assetData["data"][holding["ticker"]]["id"],
            }

            tickerList.append(holding["ticker"])
            tickerList2.append(holding["ticker"])
            data["asset_value"].append(holdingData["total"])
            polarData.append(holdingData["total"])
            data["portfolio_value"] += holdingData["total"]
            data["tabular_data"].append(holdingData)

        data["account_value"] = data["cash"] + data["portfolio_value"]
        polarData = [round(((dp / data["account_value"]) * 100), 5) for dp in polarData]
        data["percent_performance"] = ((data["account_value"] / 100000) - 1) * 100
        data["monetary_performance"] = data["account_value"] - 100000

        return render_template("index.html", data=data, tickerList=json.dumps(tickerList), tickerList2=json.dumps(tickerList2), polarData=json.dumps(polarData))


@app.route("/authentication", methods=["GET"])
def authenticate():
    session.clear()
    return render_template("auth.html")


@app.route("/auth/login", methods=["GET", "POST"])
def login():
    session.clear()

    if request.method == "POST":

        username, password = request.form.get("username"), request.form.get("password")

        if username == None or username == "":
            flash('Must provide username. Try again please.', 'error')
            return render_template("login.html")

        if password == None or password == "":
            flash('Must provide password. Try again please.', 'error')
            return render_template("login.html")

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            flash('Username and/or password was incorrect.', 'error')
            return render_template("login.html")

        session["userID"] = rows[0]["id"]

        return redirect("/")
    else:
        return render_template("login.html")


@app.route("/auth/signup", methods=["GET", "POST"])
def signup():
    session.clear()

    if request.method == "POST":
        username, password = request.form.get("username"), request.form.get("password")
        confirmation, name = request.form.get("confirmation"), request.form.get("name")

        usernames = db.execute("SELECT username FROM users")
        usernames_filtered = [account["username"] for account in usernames]

        if username == None or username == "":
            flash('Username is invalid. Try again please.', 'error')
            return render_template("signup.html")
        else:
            username = username.strip()
            if not username.isalnum():
                flash('Username must be alphanumeric.', 'error')
                return render_template("signup.html")
            elif len(username) < 3:
                flash('Username must be >= 3 characters.', 'error')
                return render_template("signup.html")
            elif username in usernames_filtered:
                flash('Username already exists.', 'error')
                return render_template("signup.html")

        if password == None or password == "":
            flash('Password is Invalid. Try again please.', 'error')
            return render_template("signup.html")
        else:
            if len(password) < 8:
                flash('Password must be >= 8 characters.', 'error')
                return render_template("signup.html")

        if confirmation == None or confirmation == "":
            flash('Password is Invalid. Try again please.', 'error')
            return render_template("signup.html")
        else:
            if password != confirmation:
                flash('Passwords do not match.', 'error')
                return render_template("signup.html")

        if name == None or name == "":
            flash('Name field is Invalid. Try again please.', 'error')
            return render_template("signup.html")
        else:
            name = name.strip()
            if not name.isalnum():
                flash('Name must be alphanumeric.', 'error')
                return render_template("signup.html")
            elif len(name) < 2:
                flash('Name must be at least 1 character.', 'error')
                return render_template("signup.html")

        db.execute("INSERT INTO users (username, hash, name) VALUES(?, ?, ?)", username, generate_password_hash(password), html.escape(name))
        return redirect("/auth/login")
    else:
        return render_template("signup.html")


@app.route("/logout", methods=["GET"])
@login_required
def logout():
    session.clear()

    return redirect("/")


@app.route("/news", methods=["GET"])
@login_required
def news():
    with urllib.request.urlopen(newsUrl) as response:
        data = json.loads(response.read().decode("utf-8"))
        articles = data["articles"]

    for article in articles:
        try:
            address = article['source']['url'].split(".")
            if len(address) == 3:
                address = '.'.join(address[-2:])
            else:
                address = article['source']['url'].split("//")[-1]

            url = f"https://logo.clearbit.com/{address}"
            response = requests.get(url)

            if response.status_code == 200:
                article['logo'] = url
            else:
                article['logo'] = "/static/branding/logo.png"
        except:
            article['logo'] = "/static/branding/logo.png"

    return render_template("news.html", data=articles)


@app.route("/marketplace", methods=["GET", "POST"])
@login_required
def marketplace():
    if request.method == "POST":
        ticker = request.form.get("ticker")
        if ticker == None or ticker == "":
            flash('Invalid Ticker', 'error')
            return render_template("marketplace.html")
        else:
            parameters = {
                'symbol': ticker.strip().upper(),
                'convert': 'USD'
            }

            params = {
                'symbol': ticker.strip().upper(),
                'time_start': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                'time_end': datetime.now().strftime('%Y-%m-%d'),
                'count': 30,
                'interval': 'daily',
            }

            params2 = {
                'symbol': ticker.strip().upper(),
                'time_start': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                'time_end': datetime.now().strftime('%Y-%m-%d'),
                'count': 30,
                'interval': 'daily',
            }

            params3 = {
                'symbol': ticker.strip().upper(),
                'time_start': (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'),
                'time_end': datetime.now().strftime('%Y-%m-%d'),
                'count': 30,
                'interval': 'daily',
            }

            try:
                response = requests.get(url_1, headers=headers, params=parameters)
                response2 = requests.get(url_2, headers=headers, params=parameters)
                response3 = requests.get(url_3, headers=headers, params=params)
                response4 = requests.get(url_3, headers=headers, params=params2)
                response5 = requests.get(url_3, headers=headers, params=params3)
            except:
                flash('Processing Error', 'error')
                return render_template("marketplace.html")
            else:
                data = response.json()
                ohlcv_data = response2.json()
                close_data = response3.json()
                data_7 = response4.json()
                data_90 = response5.json()

            try:
                if data['data'] == {} or ohlcv_data['data'] == {}:
                    flash('Invalid Ticker', 'error')
                    return render_template("marketplace.html")
            except:
                flash('Invalid Ticker', 'error')
                return render_template("marketplace.html")

            chartLabels = [(datetime.now() - timedelta(days=x)).strftime('%Y-%m-%d') for x in range(30)]
            chartLabels.reverse()

            chartData = {
                'labels': chartLabels,
                'values': [day['quote']['USD']['close'] for day in close_data['data']['quotes']]
            }

            seven_high = [day['quote']['USD']['high'] for day in data_7['data']['quotes']]
            seven_low = [day['quote']['USD']['low'] for day in data_7['data']['quotes']]
            thirty_high = [day['quote']['USD']['high'] for day in close_data['data']['quotes']]
            thirty_low = [day['quote']['USD']['low'] for day in close_data['data']['quotes']]
            ninety_high = [day['quote']['USD']['high'] for day in data_90['data']['quotes']]
            ninety_low = [day['quote']['USD']['low'] for day in data_90['data']['quotes']]

            hlData = [max(seven_high), min(seven_low), max(thirty_high), min(thirty_low), max(ninety_high), min(ninety_low)]

            return render_template("currencyData.html", data=data, ticker=parameters['symbol'], date=datetime.now().strftime("%B %d, %Y"), data2=ohlcv_data, chartData=chartData, hlData=hlData)
    else:
        return render_template("marketplace.html")


@app.route("/buy/<ticker>", methods=["GET", "POST"])
@login_required
def buy(ticker):

    parameters = {
        'symbol': ticker.strip().upper(),
        'convert': 'USD'
    }

    try:
        response = requests.get(url_1, headers=headers, params=parameters)
    except:
        flash('Processing Error', 'error')
        return render_template("marketplace.html")
    else:
        data = response.json()

    if data['data'] == {}:
        flash('Processing Error', 'error')
        return render_template("marketplace.html")

    user_data = db.execute("SELECT * FROM users WHERE id = ?", session["userID"])

    if request.method == "POST":
        if not request.form.get("units"):
            flash('Processing Error', 'error')
            return render_template("buy.html", data=data, user_data=user_data, ticker=ticker)

        units = int(request.form.get("units"))
        Balance = db.execute("SELECT cash FROM users WHERE id = ?", session["userID"])
        currentBalance = float(Balance[0]["cash"])

        if currentBalance < round((data['data'][ticker]['quote']['USD']['price'] * units), 5):
            flash('Insufficient Funds', 'error')
            return render_template("buy.html", data=data, user_data=user_data, ticker=ticker)

        assets = db.execute("SELECT * FROM holdings WHERE id = ?", session["userID"])
        SAssets = [share["ticker"] for share in assets]

        if (not SAssets) or (ticker not in SAssets):
            db.execute("INSERT INTO holdings (id, ticker, shares) VALUES(?, ?, ?)", session["userID"], ticker, units)
        else:
            current_Assets = db.execute("SELECT shares FROM holdings WHERE id = ? AND ticker = ?", session["userID"], ticker)
            db.execute("UPDATE holdings SET shares = ? WHERE id = ? AND ticker = ?", int(current_Assets[0]["shares"]) + int(units), session["userID"], ticker)

        db.execute("INSERT INTO purchases (id, ticker, shares, price, transacted, photo, name) VALUES(?, ?, ?, ?, ?, ?, ?)", session["userID"], ticker, int(units), round(data['data'][ticker]['quote']['USD']['price'], 5), datetime.now().strftime('%Y-%m-%d %H:%M:%S'), data['data'][ticker]['id'], data['data'][ticker]['name'])
        db.execute("UPDATE users SET cash = ? WHERE id = ?", (currentBalance - (round(float(data['data'][ticker]['quote']['USD']['price'] * int(units)), 5))), session["userID"])

        return redirect("/")
    else:
        return render_template("buy.html", data=data, user_data=user_data, ticker=ticker)


@app.route("/sell/<ticker>/<shares>", methods=["GET", "POST"])
@login_required
def sell(ticker, shares):

    parameters = {
        'symbol': ticker.strip().upper(),
        'convert': 'USD'
    }

    try:
        response = requests.get(url_1, headers=headers, params=parameters)
        data = response.json()

        if data['data'] == {}:
            flash('Processing Error', 'error')
            return render_template("marketplace.html")
    except:
        flash('Processing Error', 'error')
        return render_template("marketplace.html")


    user_data = db.execute("SELECT * FROM users WHERE id = ?", session["userID"])

    if request.method == "POST":
        if not request.form.get("units"):
            flash('Processing Error', 'error')
            return render_template("sell.html", data=data, user_data=user_data, ticker=ticker, shares=shares)

        units = int(request.form.get("units"))
        Balance = db.execute("SELECT cash FROM users WHERE id = ?", session["userID"])
        currentBalance = float(Balance[0]["cash"])

        SHARES = db.execute("SELECT shares FROM holdings WHERE id = ? and ticker = ?", session["userID"], ticker)

        if not (0 < units <= SHARES[0]["shares"]):
            flash('Not enough shares', 'error')
            return render_template("sell.html", data=data, user_data=user_data, ticker=ticker, shares=shares)

        db.execute("UPDATE holdings SET shares = ? WHERE id = ? AND ticker = ?", int(SHARES[0]["shares"]) - units, session["userID"], ticker)

        current_Assets = db.execute("SELECT shares FROM holdings WHERE id = ? AND ticker = ?", session["userID"], ticker)
        if (int(current_Assets[0]["shares"]) == 0):
            db.execute("DELETE FROM holdings WHERE id = ? AND ticker = ?", session["userID"], ticker)

        Balance = db.execute("SELECT cash FROM users WHERE id = ?", session["userID"])
        currentBalance = float(Balance[0]["cash"])

        db.execute("INSERT INTO purchases (id, ticker, shares, price, transacted, photo, name) VALUES(?, ?, ?, ?, ?, ?, ?)", session["userID"], ticker, (-1 * units), round(data['data'][ticker]['quote']['USD']['price'], 5), datetime.now().strftime('%Y-%m-%d %H:%M:%S'), data['data'][ticker]['id'], data['data'][ticker]['name'])
        db.execute("UPDATE users SET cash = ? WHERE id = ?", (currentBalance + (round(float(data['data'][ticker]['quote']['USD']['price'] * int(units)), 5))), session["userID"])

        return redirect("/")

    else:
        return render_template("sell.html", data=data, user_data=user_data, ticker=ticker, shares=shares)


@app.route("/history", methods=["GET"])
@login_required
def history():
    user_history = db.execute("SELECT * FROM purchases WHERE id = ?", session["userID"])

    if user_history == []:
        return render_template("history2.html")
    else:

        i = 0
        tickerList = []
        tabular_data = []
        for purchase in user_history:

            data = {
                "num": i + 1,
                "id": purchase['photo'],
                "name": purchase['name'],
                "ticker": purchase['ticker'],
                "shares": purchase['shares'] if purchase['shares'] > 0 else (-1 * purchase['shares']),
                "type": "Buy" if purchase['shares'] > 0 else "Sell",
                "price": purchase['price'],
                "total": purchase['price'] * purchase['shares'] if purchase['shares'] > 0 else purchase['price'] * (-1 * purchase['shares']),
                "transacted": purchase['transacted']
            }

            i += 1
            tickerList.append(data['num'])
            tabular_data.append(data)

        return render_template("history.html", data=tabular_data, tickerList=tickerList)

@app.route("/getNovelData", methods=["GET"])
def getNovelData():

    userInfo = db.execute("SELECT * FROM users WHERE id = ?", session["userID"])
    userFinancialInfo = db.execute("SELECT * FROM holdings WHERE id = ?", session["userID"])

    data = {
        "name": userInfo[0]["name"],
        "cash": userInfo[0]["cash"],
        "portfolio_value": 0,
        "account_value": 0,
        "assets": [],
        "asset_value": [],
        "percent_performance": 0,
        "monetary_performance": 0,
        "tabular_data": [],
        "tickerArr": request.args.get("q").split(",")
    }

    for holding in userFinancialInfo:
        data["assets"].append(holding["ticker"])

        parameters = {
            'symbol': holding["ticker"],
            'convert': 'USD'
        }

        response = requests.get(url_1, headers=headers, params=parameters)
        assetData = response.json()

        holdingData = {
            "name": assetData["data"][holding["ticker"]]["name"],
            "ticker": holding["ticker"],
            "shares": holding["shares"],
            "pc": assetData["data"][holding["ticker"]]["quote"]["USD"]["percent_change_24h"],
            "price": assetData["data"][holding["ticker"]]["quote"]["USD"]["price"],
            "total": assetData["data"][holding["ticker"]]["quote"]["USD"]["price"] * holding["shares"],
            "id": assetData["data"][holding["ticker"]]["id"],
        }

        data["asset_value"].append(holdingData["total"])
        data["portfolio_value"] += holdingData["total"]
        data["tabular_data"].append(holdingData)

    data["account_value"] = data["cash"] + data["portfolio_value"]
    data["percent_performance"] = ((data["account_value"] / 100000) - 1) * 100
    data["monetary_performance"] = data["account_value"] - 100000

    return jsonify(data)
