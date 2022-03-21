import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import datetime

from support import apology, login_required, usd, lookupcrypto, cryptonews

# Types of currency to be selected in quote
cryptolist = {1: "BTC", 2: "ETH", 3: "XRP", 4: "BNB", 5: "ADA", 6: "DOT"}

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of cryptocoins"""
    # query all coins in the user's portfolio

    crypto = db.execute("select userid, symbol, shares from portfolio where userid=?", session["user_id"])
    rows = db.execute("select cash from users where id=?", session["user_id"])
    cash = float(rows[0]["cash"])
    totalcrypto = 0
    portfolio = crypto

    for i in range(0, len(crypto)):
        aux = lookupcrypto(crypto[i]["symbol"])
        portfolio[i]["price"] = aux["price"]
        portfolio[i]["total"] = float(aux["price"].replace(',', '').replace('$', ''))*crypto[i]["shares"]
        totalcrypto = totalcrypto + portfolio[i]["total"]

    totalport = cash + totalcrypto

    return render_template("index.html", portfolio=portfolio, cash=cash, totalcrypto=totalcrypto, totalport=totalport)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of coins"""
    # user is redirected via GET
    if request.method == "GET":
        return render_template("buy.html", cryptolist=cryptolist)
    else:
        quote = lookupcrypto(request.form.get("symbol"))
        amount = request.form.get("amount")
        # return error message if crpto does not exist and if the amount is invalid
        if quote == None:
            flash("Please select a crypto coin.")
            return redirect("/buy")
        elif (amount == "" or amount.isnumeric() == False):
            flash("You entered an invalid amount.")
            return redirect("/buy")
        elif float(amount) <= 0:
            flash("The amount must be greater than 0.")
            return redirect("/buy")

        amount = float(amount)

        # check if user has enough funds to buy shares
        rows = db.execute("SELECT * FROM users WHERE id=?", session["user_id"])
        result = rows[0]["cash"] - amount
        #(amount *  float(quote["price"].replace(',', '').replace('$', '')))
        # user does not have enough funds to proceed with the purchase
        if result < 0:
            flash("You do not have enough cash.")
            return redirect("/buy")
        else:
            # log purchase into the purchase database
            shares = round(amount / float(quote["price"].replace(',', '').replace('$', '')), 2)
            db.execute("INSERT INTO purchases (userid,symbol,shares,shareprice, datetime) VALUES (?,?,?,?,?)",
                       session["user_id"], quote["symbol"], shares, float(quote["price"].replace(',', '').replace('$', '')), datetime.datetime.now())
            # reduce the cash position of the customer
            db.execute("UPDATE users SET cash=? WHERE id=?", result, session["user_id"])

            # update the portfolio
            portfolio = db.execute("select userid, symbol, shares from portfolio where userid=? and symbol=?",
                                   session["user_id"], quote["symbol"])
            if not portfolio:
                db.execute("INSERT INTO portfolio (userid, symbol, shares) VALUES (?,?,?)",
                           session["user_id"], quote["symbol"], shares)
            else:
                db.execute("UPDATE portfolio SET shares=? WHERE userid=? and symbol=?",
                           (shares+portfolio[0]["shares"]), session["user_id"], quote["symbol"])

        flash("Bought! Transaction is successful!")

        # Redirect user to home page
        return redirect("/")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    purchases = sales = {}
    # query all purchases
    purchases = db.execute("SELECT * FROM purchases WHERE userid=? ORDER BY datetime DESC", session["user_id"])
    # add transaction id for purchase
    for i in range(0, len(purchases)):
        purchases[i]["transaction"] = "buy"

    # query all sales
    sales = db.execute("SELECT * FROM sales WHERE userid=? ORDER BY datetime DESC", session["user_id"])
    # add transaction id for sales
    for i in range(0, len(sales)):
        sales[i]["transaction"] = "sales"

    # display in the history.html
    alltransactions = purchases + sales

    return render_template("history.html", alltransactions=alltransactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("Must provide an username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("Must provide a password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Store lastlogin to present in the welcome message
        lastlogin = rows[0]["lastlogin"]
        # Update lastlogin field in the database with the new lastlogin
        db.execute("UPDATE users SET lastlogin=? WHERE id=?", rows[0]["id"], datetime.datetime.now())

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to dashboard with an welcome back message
        flash("Welcome back " + str(request.form.get("username").capitalize()) + "!  Your last login was " + str(lastlogin) + ".")
        return redirect("/dashboard")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("/login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return render_template("/login.html")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():

    # User reached route via GET
    if request.method == "GET":
        return render_template("quote.html", cryptolist=cryptolist)
    # User reached route via POST
    else:

        symbol = request.form.get("symbol")
        if symbol == None:
            # return error message if crypto does not exist
            flash("Select a cryptocoin and a currency")
            # Redirect user to home page
            return redirect("/quote")

        else:
            # look up cryto currency info and pass to quote page
            quote = lookupcrypto(symbol)
            return render_template("quote.html", cryptolist=cryptolist, quote=quote, symbol=symbol)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # Forget any user_id
    session.clear()

    if request.method == "GET":
        return render_template("register.html")
    else:
        # Ensure username was submitted
        if not request.form.get("username") or request.form.get("username") == "":
            return apology("must provide username", 400)

        # Check if the username is available
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        if len(rows) == 1:
            return apology("Username is not available", 400)

        # Ensure password was submitted
        elif not request.form.get("password") or not request.form.get("confirmation"):
            return apology("Please provide a password and confirm it", 400)

        # Ensure password contains more than 8 digits
        elif len(request.form.get("password")) < 8:
            return apology("Passwords must contain minimum of 8 digits", 400)

        # Ensure passwords 1 and 2 match
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("The passwords do not match.", 400)

        # Add user and password to the database
        db.execute("INSERT INTO users (username, hash, lastlogin) VALUES (?,?,?)",
                   request.form.get("username"), generate_password_hash(request.form.get("password"), "sha256"), datetime.datetime.now())
        rows = db.execute("SELECT * from users where username=?", request.form.get("username"))

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to dashboard with an welcome message
        flash("Welcome " + str(request.form.get("username").capitalize()) + "!")
        return redirect("/dashboard")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of coins"""
    # query the coins the customer owns and quantity
    rows = db.execute("select userid, symbol, shares from portfolio where userid=?", session["user_id"])

    # select only the coin symbols to pass as the select menu in buy.html
    crypto = {}
    for i in range(len(rows)):
        crypto[i] = rows[i]["symbol"]

    # user is redirected via GET
    if request.method == "GET":
        return render_template("sell.html", crypto=crypto)
    else:

        crypto = request.form.get("symbol")
        amount = request.form.get("amount")

        # return error message if coin was not entered or number of shares is less than 0 or null
        if crypto == None:
            flash("Please select a crypto coin.")
            return redirect("/sell")
        elif amount == "" or isinstance(amount, float) == True:
            flash("You entered an invalid number.")
            return redirect("/sell")
        elif float(amount) <= 0:
            flash("Amount must be greater than 0.")
            return redirect("/sell")

        # convert shares to an integer
        amount = float(amount)
        currentshares = 0

        # retrieve the number of shares user currently owns
        for i in range(0, len(rows)):
            if rows[i]["symbol"] == crypto:
                currentshares = rows[i]["shares"]

        # check if the user has enough shares of the coin
        quote = lookupcrypto(request.form.get("symbol"))
        if amount <= (currentshares * float(quote["price"].replace(',', '').replace('$', ''))):

            # log the coin sale into the sales database
            shares = round(amount / float(quote["price"].replace(',', '').replace('$', '')), 2)
            db.execute("INSERT INTO sales (userid,symbol,shares,shareprice,datetime) VALUES (?,?,?,?,?)",
                       session["user_id"], crypto, shares, quote["price"], datetime.datetime.now())

            # increase the cash position of the customer based on the coin current price
            rows = db.execute("SELECT * FROM users WHERE id=?", session["user_id"])
            newcash = rows[0]["cash"] + amount
            db.execute("UPDATE users SET cash=? WHERE id=?", newcash, session["user_id"])

            # update portfolio of crypto coins
            currentshares = currentshares - shares
            if currentshares > 0:
                db.execute("UPDATE portfolio SET shares=? WHERE userid=? and symbol=?",
                           currentshares, session["user_id"], crypto)
            else:
                db.execute("DELETE FROM portfolio WHERE userid=? and symbol=?", session["user_id"], crypto)

            flash("Sold! Transaction is succesful!")
            return redirect("/")

        else:
            flash("Not enough crypto currency.")
            return redirect("/sell")


@app.route("/changepassword", methods=["GET", "POST"])
@login_required
def changepassword():

    if request.method == "GET":
        return render_template("changepassword.html")
    else:
        # Ensure password was submitted
        if not request.form.get("password1") or not request.form.get("password2"):
            return apology("Please provide a password and confirm it", 400)

        # Ensure password contains more than 8 digits
        elif len(request.form.get("password1")) < 8:
            return apology("Passwords must contain minimum of 8 digits", 400)

        # Ensure passwords 1 and 2 match
        elif request.form.get("password1") != request.form.get("password2"):
            return apology("The passwords do not match.", 400)

        # Ensure new password is different than current
        rows = db.execute("SELECT hash FROM users WHERE id=?", session["user_id"])
        currenthash = rows[0]["hash"]
        if check_password_hash(currenthash, request.form.get("password1")):
            return apology("New password must be different than existing one.", 400)
        else:
            # Update password in the database
            newhash = generate_password_hash(request.form.get("password1"), "sha256")
            db.execute("UPDATE users SET hash=? WHERE id=?", newhash, session["user_id"])
            flash("Password has been reset!")
            return redirect("/dashboard")


@app.route("/addcash", methods=["GET", "POST"])
@login_required
def addcash():
    if request.method == "GET":
        return render_template("addcash.html")
    else:
        cash = request.form.get("cash_to_add")
        # check for 0, blank or negative cash amount input by user
        if cash == None:
            return apology("Please enter the cash amount", 400)
        elif cash == "":
            return apology("Please enter the cash amount", 400)
        elif float(cash) <= 0:
            return apology("Please enter the cash amount greater than $0", 400)
        # retrieve currnet cash amount from the database
        row = db.execute("SELECT cash FROM users WHERE id=?", session["user_id"])

        cash = float(cash) + float(row[0]["cash"])

        # Update new cash amount in the user database
        db.execute("UPDATE users SET cash=? WHERE id=?", cash, session["user_id"])
        flash("Cash has been added to your account")
        return redirect("/")


@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():

    dashboard = {}
    for i in range(1, len(cryptolist)):
        dashboard[cryptolist[i]] = lookupcrypto(cryptolist[i])

    news = cryptonews()
    return render_template("dashboard.html", dashboard=dashboard, news=news['Data'])


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)