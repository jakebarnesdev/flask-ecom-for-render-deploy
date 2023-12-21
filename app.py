from flask import Flask, render_template, request, send_from_directory, url_for
import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from helpers import apology, login_required, lookup, usd

app = Flask(__name__)
db = SQL("sqlite:///database.db")
app.secret_key = 'your_secret_key_here'
app.secret_key = os.urandom(24)

@app.route('/')
def index():
    # query for 3 random shirts that are not repeat designs
    random_designs = db.execute("SELECT * FROM Stock GROUP BY Design ORDER BY RANDOM() LIMIT 3;")
    # this varible can then be looped through in webapge
    return render_template('index.html', random_designs=random_designs)

@app.route('/about')
def about():
    # a simple static page
    return render_template('about.html')

@app.route('/account')
def account():
    # check if logged in by checking session
    if 'user_id' not in session:
        # redirect to the login page
        return redirect(url_for('login'))
    # return user id
    id_return = session['user_id']
    # query for current users id
    username = db.execute("SELECT username FROM users WHERE id = ?", id_return)
    # query for current users puchase history and create a list of dictionaries containing purchase info
    purchase_query = db.execute("SELECT PurchaseHistory.*, Stock.Type, Stock.Size, Stock.Color, Stock.Price, Stock.Design FROM PurchaseHistory JOIN Stock ON PurchaseHistory.ProductID = Stock.ID WHERE PurchaseHistory.UserID = ?", id_return)
    # initialize an empty dictionary
    grouped_entries = {}
    # iterate through the purchase_query list
    for entry in purchase_query:
        # return timestamp variable
        timestamp = entry['PurchaseDate']
        # check if timestamp exists in the dictionary 
        if timestamp in grouped_entries:
            # use key to add to a current list of purchases
            grouped_entries[timestamp].append(entry)
        else:
            # create a new key for a list of purchases
            grouped_entries[timestamp] = [entry]
    # init a list with to contain grouped results and summed orders
    grouped_result = []

    for timestamp in grouped_entries:
        # get the list of entries for the current timestamp
        entries = grouped_entries[timestamp]
        # variable for total amount
        total_amount = 0 
        # iterate over each entry in the list of entries for the current timestamp
        for entry in entries:
            # accumulate total amount
            total_amount += entry['TotalAmount']
        # append grouped info and total sum to grouped_result in for the form of a dictionary
        grouped_result.append({
            'PurchaseDate': timestamp,
            'GroupedEntries': entries,
            'TotalAmountSum': total_amount
        })
    # with this grouped_result variable we can loop through it in the html, display the puchse date for a paticular order, then loop through the entires linked to that date, and display the total cost of the order.

    return render_template('account.html', grouped_result=grouped_result, username=username)


@app.route('/purchase_complete')
def purchase_complete():
    # check if logged in by checking session
    if 'user_id' not in session:
        # redirect to the login page
        return redirect(url_for('login'))
    # query for current users id
    id_return = session['user_id']
    # query for order to be completed
    existing_order = db.execute("SELECT basket.*, stock.Price, stock.Quantity FROM basket JOIN stock ON basket.ProductID = stock.ID WHERE basket.UserID = ?", id_return)
    # iterate through the existing order results
    for order in existing_order:
        # gather data for each entry
        id_return = order['UserID']
        product_id = order['ProductID']
        quantity = order['QuantityBuying']
        stock_quantity = order['Quantity']
        purchase_date = datetime.now()
        total_amount = order['Price'] * quantity

        # stock check
        if stock_quantity < quantity:
            return apology("Not enough stock")

        # update stock quantity for current product
        updated_stock_quantity = stock_quantity - quantity
        db.execute("UPDATE Stock SET Quantity = ? WHERE ID = ?", updated_stock_quantity, product_id)

        # create entry in PurchaseHistory
        db.execute("INSERT INTO PurchaseHistory(UserID, ProductID, Quantity, PurchaseDate, TotalAmount) VALUES(?, ?, ?, ?, ?)",
                id_return, product_id, quantity, purchase_date, total_amount)

        # get id for order
        basket_item_id = order['ID']
        # delete order entry from basket
        db.execute("DELETE FROM Basket WHERE ID = ?", basket_item_id)
    # once the for loop is complete the stock table with have the correct quanitties, a record will be added to the puchase historty stock table, and the order will be removed from the basket table 
    return render_template('purchase_complete.html')


@app.route('/checkout')
def checkout():
    # check if logged in by checking session
    if 'user_id' not in session:
        # redirect to the login page
        return redirect(url_for('login'))
    # query for current users id
    id_return = session['user_id']
    # query items in basket with user return prouct information
    basket_items = db.execute("SELECT basket.id, stock.*, basket.QuantityBuying FROM basket JOIN stock ON basket.ProductID = stock.ID WHERE userID = ?", id_return)
    # init total price
    total_price = 0
    # iterate over items in 
    for item in basket_items:
        # muliplty original price buy quanityty and accumilite for each item
        total_price += (item['Price'] * item['QuantityBuying'])  
    # the total price variable is calculated and can be displayed in the html
    return render_template('checkout.html', total_price=total_price)

@app.route('/basket')
def basket():
    session['return_page'] = '/basket'
    # check if logged in by checking session
    if 'user_id' not in session:
        # redirect to the login page
        return redirect(url_for('login'))
    # query for current users id
    id_return = session['user_id']
    # query items in basket with user return prouct information
    basket_items = db.execute("SELECT basket.id, stock.*, basket.QuantityBuying FROM basket JOIN stock ON basket.ProductID = stock.ID WHERE userID = ?", id_return)
    # init total price
    total_price = 0
    # iterate over items in 
    for item in basket_items:
        # muliplty original price buy quanityty and accumilite for each item
        total_price += (item['Price'] * item['QuantityBuying']) 
    # with theese variables in the html we can loop through every item the customer has addded to thier basket anddisplaay a calculated total price
    return render_template('basket.html', basket_items=basket_items, total_price=total_price)


@app.route('/remove_item/<int:item_id>', methods=['POST'])
def remove_item(item_id):
    # check if logged in by checking session
    if 'user_id' not in session:
        # redirect to the login page
        return redirect(url_for('login'))
    # query for current users id
    id_return = session['user_id']

    # get the quantity rquested from user to remove
    quantity_to_remove = int(request.form.get('quantity', 1))

    # query for item and order
    existing_quantity = db.execute("SELECT QuantityBuying FROM basket WHERE userID = ? AND ProductID = ?", id_return, item_id)

    if existing_quantity:
        # condiditon for removing 
        if quantity_to_remove < int(existing_quantity[0]['QuantityBuying']):
            # the the quanitiy of items being removed is less than the existing quntity the entry is updated by subtracting quantity_to_remove from QuantityBuying
            db.execute("UPDATE basket SET QuantityBuying = QuantityBuying - ? WHERE userID = ? AND ProductID = ?", quantity_to_remove, id_return, item_id)
        else:
            # if the number is equal to or larger than the amount the entry is removed
            db.execute("DELETE FROM basket WHERE userID = ? AND ProductID = ?", id_return, item_id)

    # redirect user back to the basket page after tables are updated
    return redirect(url_for('basket'))

@app.route('/add_to_basket', methods=['POST'])
def add_to_basket():
    # check if logged in by checking session
    if 'user_id' not in session:
        # redirect to the login page
        return redirect(url_for('login'))
    # query for current users id
    id_return = session['user_id']
    # get id and quntity from HTML
    product_id = int(request.form['product_id'])
    quantity = int(request.form['quantity'])

    # query quantity of stock
    stock_quantity = db.execute("SELECT Quantity FROM Stock WHERE ID = ?", product_id)

    # check if query found product
    if not stock_quantity:
        return apology("Product not found in stock")
    
    # check of product is in existing baskets
    basket_quantity = db.execute("SELECT QuantityBuying FROM Basket WHERE ProductID = ?", product_id)
    # init basket quantity int
    total_basket_quantity = 0
    # loop through instances products in baskets
    for instance in basket_quantity:
        # update for each instance
        total_basket_quantity += instance['QuantityBuying']

    # check if the stock in the database is sufficent
    if stock_quantity[0]['Quantity'] < quantity + total_basket_quantity:
        return apology("Insufficient stock")

    # query for user already having produt in basket
    existing_order = db.execute("SELECT * FROM basket WHERE UserID = ? AND ProductID = ?", id_return, product_id)
    

    if existing_order:
        # get order id
        Order_id = existing_order[0]['ID']
        # update quantity
        new_quantity = existing_order[0]['QuantityBuying'] + quantity
        # update database
        db.execute("UPDATE basket SET QuantityBuying = ? WHERE ID = ?", new_quantity, Order_id)
    else:
        # if not in basked make instert order
        db.execute("INSERT INTO basket (UserID, ProductID, QuantityBuying) VALUES (?, ?, ?)", id_return, product_id, quantity)
    return redirect(url_for('basket'))




@app.route('/product_render/<design>', methods=['GET'])
def product_render(design):
    # query product
    product = db.execute("SELECT * FROM stock WHERE Design = ?", design)

    if not product:
        # Handle the case where the product is not found
        return apology("product not found", 403)
    
    # get stock quantity
    stock_quantity = product[0]['Quantity']
    # init in_stock bool
    in_stock = False
    # read quantity and update bool
    if stock_quantity > 0:
        in_stock = True
    # init stock left int
    stock_left = 11
    # check if stock left needs to be displayed in page through checking stock_quantity
    if stock_quantity <= 10 and stock_quantity > 0:
        # if the quanatiy of stock need to be rendered on the webpage update stock left to whatever number less that 11 it may be
        stock_left = stock_quantity
    # for this page we have all of the product information, an inteiger for stock left of the proudct, and a boolean  for it the product is in stock so we can render what information that meets the conditions set in the html page
    return render_template('product_render.html', product=product, stock_left=stock_left, in_stock=in_stock)

@app.route('/product_list', methods=['GET', 'POST'])
def product_list():
    # store page in session
    session['return_page'] = '/product_list'

    # query for every design
    products = db.execute("SELECT * FROM stock WHERE Design IS NOT NULL")

    if request.method == 'POST':
        # get category from filter form
        selected_category = request.form.get('category', None)

        # check if categories will be filtered
        if selected_category:
            # query for selected categories update, procuts
            products = db.execute("SELECT * FROM stock WHERE Design IS NOT NULL AND Style = ?", (selected_category,))

        # filter by maximum price
        max_price = int(request.form.get('min_price', 100)) # update variable name
        new_products = []
        # iterate through prodcts
        for product in products:
            # check product price against filtered price
            if product['Price'] <= max_price:
                # if price condition is met append to new_proudcts
                new_products.append(product)
        # update products
        products = new_products
    # to filter from navbar
    elif request.method == 'GET':
        selected_category = request.args.get('category')
        if selected_category:
            products = db.execute("SELECT * FROM stock WHERE Design IS NOT NULL AND Style = ?", (selected_category,))
    # with products sent to the html we can loop through and display proucts onto our page, meeting the filter conditions if needed
    return render_template('product_list.html', products=products)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    session.clear()
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user
        return_page = session.get('return_page', '/')
        return redirect(return_page)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")



@app.route("/logout")
def logout():
    """Log user out"""

    # Clear the basket for the current user
    id_return = session.get("user_id")
    if id_return:
        db.execute("DELETE FROM Basket WHERE UserID = ?", id_return)

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    session.clear()

    if request.method == "POST":
        # check username length
        username = request.form.get("username")
        if not username or len(username) < 4:
            return apology("username must have at least 4 characters", 400)

        # check password was provided
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # check password confirmation was provided
        elif not request.form.get("confirmation"):
            return apology("must confirm password", 400)

        # check for matching password and confirmation
        elif request.form.get("confirmation") != request.form.get("password"):
            return apology("passwords do not match", 400)

        # check database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", username
        )

        # check if rows find a username
        if len(rows) != 0:
            return apology("Choose a new username, this username already exists", 400)

        # hash password
        hashed_password = generate_password_hash(
            request.form.get("password"), method="pbkdf2", salt_length=16
        )

        # add hashed password to database
        db.execute(
            "INSERT INTO users(username, hash) VALUES(?, ?)",
            username,
            hashed_password,
        )

        # sign in session
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", username
        )

        # add user
        session["user_id"] = rows[0]["id"]

        return redirect("/")

    else:
        return render_template("register.html")
    
if __name__ == '__main__':
    # Use the PORT environment variable if available, otherwise default to 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
