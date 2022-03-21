import os
import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"


def lookupcrypto(symbol):
    # Contact API
    """uses API from cryptocompare website"""
    try:
        api_key = os.environ.get("API_KEY")
        url = f"https://min-api.cryptocompare.com/data/pricemultifull?fsyms={symbol}&tsyms=USD"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        quote = response.json()
        return {
            "symbol": symbol,
            "price": quote["DISPLAY"][symbol]["USD"]['PRICE'],
            "mktcap": quote["DISPLAY"][symbol]["USD"]['MKTCAP'],
            "imageurl": quote["DISPLAY"][symbol]["USD"]['IMAGEURL'],
            "changepctday": quote["DISPLAY"][symbol]["USD"]['CHANGEPCTDAY'],
            "high24h": quote["DISPLAY"][symbol]["USD"]['HIGH24HOUR'],
            "low24h": quote["DISPLAY"][symbol]["USD"]['LOW24HOUR']
        }

    except (KeyError, TypeError, ValueError):
        return None


def cryptonews():
    # Contact API
    try:
        api_key = os.environ.get("API_KEY")
        url = f"https://min-api.cryptocompare.com/data/v2/news/?lang=EN"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response containing dict called news
    try:
        news = response.json()
        return news

    except requests.RequestException:
        return None