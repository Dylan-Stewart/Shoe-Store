import psycopg2
import random
import time
from datetime import datetime

# connect
connection = psycopg2.connect("dbname=postgres user=postgres password=admin")
cur = connection.cursor()

# make stocks table
cur.execute('''
    CREATE TABLE IF NOT EXISTS Stocks (
        shoe_id INT PRIMARY KEY REFERENCES Shoes(shoe_id),
        quantity INT NOT NULL
    );
''')

connection.commit()

# add random stock to random products
def add_stock():
    cur.execute('SELECT shoe_id FROM Shoes;')
    shoe_ids = [shoe[0] for shoe in cur.fetchall()]

    # randomizer
    random.shuffle(shoe_ids)

    for shoe_id in shoe_ids:
        random_quantity = random.randint(1, 1000)
        cur.execute('''
            INSERT INTO Stocks (shoe_id, quantity)
            VALUES (%s, %s)
            ON CONFLICT (shoe_id) DO UPDATE
            SET quantity = Stocks.quantity + %s;
        ''', (shoe_id, random_quantity, random_quantity))

    connection.commit()

# check if a product is in stock
def is_product_in_stock(shoe_id, quantity):
    cur.execute('SELECT quantity FROM Stocks WHERE shoe_id = %s;', (shoe_id,))
    stock_quantity = cur.fetchone()
    return stock_quantity is not None and stock_quantity[0] >= quantity

# decrease stock after an item is sold
def decrease_stock(shoe_id, quantity):
    cur.execute('UPDATE Stocks SET quantity = quantity - %s WHERE shoe_id = %s;', (quantity, shoe_id))
    connection.commit()

# generate a random order
def generate_order():
    cur.execute('SELECT customer_id FROM Customers ORDER BY RANDOM() LIMIT 1;')
    customer_id = cur.fetchone()[0]

    cur.execute('SELECT shoe_id FROM Shoes ORDER BY RANDOM() LIMIT 1;')
    shoe_id = cur.fetchone()[0]

    cur.execute('SELECT quantity FROM Stocks WHERE shoe_id = %s;', (shoe_id,))
    stock_quantity = cur.fetchone()[0]

    # constrain the random product quantity to available quantity
    order_quantity = random.randint(1, min(stock_quantity, 1000))

    return customer_id, shoe_id, order_quantity

# place an order
def place_order(customer_id, shoe_id, quantity):
    if is_product_in_stock(shoe_id, quantity):
        cur.execute('''
            INSERT INTO Orders (customer_id, order_date, total_amount)
            VALUES (%s, NOW(), 0)
            RETURNING order_id;
        ''', (customer_id,))
        order_id = cur.fetchone()[0]

        cur.execute('SELECT price FROM Shoes WHERE shoe_id = %s;', (shoe_id,))
        price = cur.fetchone()[0]

        cur.execute('''
            INSERT INTO OrderDetails (order_id, shoe_id, quantity, price)
            VALUES (%s, %s, %s, %s);
        ''', (order_id, shoe_id, quantity, price))

        # decrease stock after order
        decrease_stock(shoe_id, quantity)

        connection.commit()
        print(f"Order placed for Customer {customer_id}: {quantity} pairs of Shoe {shoe_id}")
    else:
        print(f"Product with shoe_id {shoe_id} is out of stock. No order placed.")

# main
while True:
    try:
        X = 20
        # add the stock
        add_stock()

        # place random order
        order = generate_order()
        if order:
            customer_id, shoe_id, quantity = order
            place_order(customer_id, shoe_id, quantity)

        # sleep X seconds
        time.sleep(X)
    except Exception as e:
        print(f"Error {e}")
