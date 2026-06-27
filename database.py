import pandas as pd
import psycopg2
import streamlit as st

def get_conn():
    url = st.secrets["DATABASE_URL"]
    return psycopg2.connect(url, sslmode="require")

def setup_database():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS Menu (
        item_id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price INTEGER NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Sales (
        order_id SERIAL PRIMARY KEY,
        item_name TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        item_total INTEGER NOT NULL,
        timestamp TIMESTAMPTZ DEFAULT NOW())''')
    cursor.execute("SELECT COUNT(*) FROM Menu")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO Menu (name, category, price) VALUES (%s, %s, %s)", [
            ('Masala Chai','Beverage',20),
            ('Filter Coffee','Beverage',30),
            ('Cold Coffee','Beverage',80),
            ('Mango Lassi','Beverage',60),
            ('Samosa','Snack',30),
            ('Vada Pav','Snack',20),
            ('Paneer Tikka Sandwich','Snack',90),
            ('Bun Maska','Snack',40),
            ('Gulab Jamun','Dessert',40),
            ('Black Forest Pastry','Dessert',70)
        ])
    conn.commit()
    cursor.close()
    conn.close()

@st.cache_data(ttl=60)
def fetch_menu_data():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM Menu ORDER BY category, name", conn)
    conn.close()
    return df

@st.cache_data(ttl=30)
def fetch_sales_data():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM Sales ORDER BY timestamp DESC", conn)
    conn.close()
    return df

def record_transaction(cart_df: pd.DataFrame):
    conn = get_conn()
    cursor = conn.cursor()
    for _, row in cart_df.iterrows():
        cursor.execute(
            "INSERT INTO Sales (item_name, quantity, item_total) VALUES (%s, %s, %s)",
            (row['name'], int(row['quantity']), int(row['subtotal']))
        )
    conn.commit()
    cursor.close()
    conn.close()

def update_menu_item(item_id: int, new_name: str, new_price: int):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE Menu SET name=%s, price=%s WHERE item_id=%s",
        (new_name, new_price, item_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

def add_menu_item(name: str, category: str, price: int):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Menu (name, category, price) VALUES (%s, %s, %s)",
        (name, category, price)
    )
    conn.commit()
    cursor.close()
    conn.close()

def delete_menu_item(item_id: int):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Menu WHERE item_id=%s", (item_id,))
    conn.commit()
    cursor.close()
    conn.close()