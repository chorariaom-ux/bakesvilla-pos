code = '''import sqlite3
import pandas as pd

DB_NAME = "cafe_billing.db"

def setup_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS Menu (item_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, category TEXT NOT NULL, price INTEGER NOT NULL)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS Sales (order_id INTEGER PRIMARY KEY AUTOINCREMENT, item_name TEXT NOT NULL, quantity INTEGER NOT NULL, item_total INTEGER NOT NULL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    cursor.execute("SELECT COUNT(*) FROM Menu")
    if cursor.fetchone()[0] == 0:
        items = [("Masala Chai","Beverage",20),("Filter Coffee","Beverage",30),("Cold Coffee","Beverage",80),("Mango Lassi","Beverage",60),("Samosa","Snack",30),("Vada Pav","Snack",20),("Paneer Tikka Sandwich","Snack",90),("Bun Maska","Snack",40),("Gulab Jamun","Dessert",40),("Black Forest Pastry","Dessert",70)]
        cursor.executemany("INSERT INTO Menu (name, category, price) VALUES (?, ?, ?)", items)
    conn.commit()
    conn.close()

def fetch_menu_data():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM Menu ORDER BY category, name", conn)
    conn.close()
    return df

def fetch_sales_data():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM Sales ORDER BY timestamp DESC", conn)
    conn.close()
    return df

def record_transaction(cart_df):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    for _, row in cart_df.iterrows():
        cursor.execute("INSERT INTO Sales (item_name, quantity, item_total) VALUES (?, ?, ?)", (row["name"], row["quantity"], row["subtotal"]))
    conn.commit()
    conn.close()

def update_menu_item(item_id, new_name, new_price):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE Menu SET name = ?, price = ? WHERE item_id = ?", (new_name, new_price, item_id))
    conn.commit()
    conn.close()

def add_menu_item(name, category, price):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Menu (name, category, price) VALUES (?, ?, ?)", (name, category, price))
    conn.commit()
    conn.close()

def delete_menu_item(item_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Menu WHERE item_id = ?", (item_id,))
    conn.commit()
    conn.close()
'''

with open("database.py", "w", encoding="utf-8") as f:
    f.write(code)

print("database.py written successfully!")
