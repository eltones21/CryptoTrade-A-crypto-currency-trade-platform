# CryptoTrade - A crypto currency trade platform
#### Video Demo:  https://youtu.be/vDV-Y1aXCn0
#### Description:
A. This project was developed on the IDE from CS50 and uses Pyhton, SQL, Jinja, Flask, HTML, CSS, AJAX, and boostrap.
B. The software has several funcionalities including:
    1. Login page - user logs in with username and password. It will check if the user inputed a valid and available username and password and present a apology page with error message.
    2. Register page - where user will be able to create an account. Requires user to enter and confirm a password that must contain 8 digits.
    3. API- uses API from Cryptocompare and connected using JSON
    4. Dashboard
        - displays the 5 largest bitcoins by mkt cap are displayed with useful trade information.
        - contains a news feed pulling API and displayin using bootstrap cards that are dynamic.
        - first page displayed after customer logs in. It displays a welcome and welcome message and when was the user's last login.
    5.Portfolio
        - user can see the information about the cryptocurrency owned
        - also it contains a shortcut to buy more or sell shares  or to add cash to the account
    6. Quote
        - page where user can select a crypto currency and see quote and basic information about the coin
        - note that quote presents the quote result in the same page using a if condition in kinja
    7.Buy/Sell/Cash
        - these 3 pages basically allows users to buy and sell currency from a list or add more cash to the account
    8. History
        - user can see a history of all the purchases or sales made since the account was opened
    9. Change password
        - user is able to modify an existing password

C. The project contains the following files:
    1. application.py - python file containing the main application (CONTROLLER)
    2. support.py - python file containing the main application (CONTROLLER)
    2. support.py - contains the API connnections with cryptocompare. Contains function for the cryptocurrency information, and for the data used for the crypto news feed.
    3. finance.db - where all the data is stored and updated. (MODEL)
        - 4 main databases: users, purchases, sales, and portfolio
    4. Templates (VIEW)
        - login.html
        - dashboard.html
        - index.html
        - addcash.html
        - quote.html
        - register.html
        - sell.html
        - buy.html
        - changepassword.html
        - history.html
        - apology.html
        - layout.html
    5.Static (VIEW)
        -styles.css

