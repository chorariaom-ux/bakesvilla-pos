import pandas as pd
import streamlit as st
import os

# --- AUTO DETECT: Use SQLite locally, Supabase on cloud ---
IS_LOCAL = os.path.exists('.streamlit/secrets.toml') and 'DATABASE_URL' not in st.secrets if hasattr(st, 'secrets') else True

if IS_LOCAL:
    import sqlite3
    DB_NAME = 'cafe_billing.db'

    def get_conn():
        return sqlite3.connect(DB_NAME)

    def setup_database():
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS Menu (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, category TEXT NOT NULL, price INTEGER NOT NULL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS Sales (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL, quantity INTEGER NOT NULL,
            item_total INTEGER NOT NULL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        cursor.execute("SELECT COUNT(*) FROM Menu")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("INSERT INTO Menu (name, category, price) VALUES (?, ?, ?)", [
                ('Masala Chai','Beverage',20),('Filter Coffee','Beverage',30),
                ('Cold Coffee','Beverage',80),('Mango Lassi','Beverage',60),
                ('Samosa','Snack',30),('Vada Pav','Snack',20),
                ('Paneer Tikka Sandwich','Snack',90),('Bun Maska','Snack',40),
                ('Gulab Jamun','Dessert',40),('Black Forest Pastry','Dessert',70)
            ])
        conn.commit()
        conn.close()

    def fetch_menu_data():
        conn = get_conn()
        df = pd.read_sql_query("SELECT * FROM Menu ORDER BY category, name", conn)
        conn.close()
        return df

    def fetch_sales_data():
        conn = get_conn()
        df = pd.read_sql_query("SELECT * FROM Sales ORDER BY timestamp DESC", conn)
        conn.close()
        return df

   def record_transaction(cart_df):
        from datetime import datetime, timezone, timedelta
        IST = timezone(timedelta(hours=5, minutes=30))
        ist_time = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')
        conn = get_conn()
        cursor = conn.cursor()
        for _, row in cart_df.iterrows():
            cursor.execute(
                "INSERT INTO Sales (item_name, quantity, item_total, timestamp) VALUES (?, ?, ?, ?)",
                (row['name'], int(row['quantity']), int(row['subtotal']), ist_time)
            )
        conn.commit()
        conn.close()

    def update_menu_item(item_id, new_name, new_price):
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("UPDATE Menu SET name=?, price=? WHERE item_id=?", (new_name, new_price, item_id))
        conn.commit()
        conn.close()

    def add_menu_item(name, category, price):
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Menu (name, category, price) VALUES (?, ?, ?)", (name, category, price))
        conn.commit()
        conn.close()

    def delete_menu_item(item_id):
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Menu WHERE item_id=?", (item_id,))
        conn.commit()
        conn.close()

else:
    import psycopg2

    def get_conn():
        return psycopg2.connect(st.secrets["DATABASE_URL"], sslmode="require")

    def setup_database():
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS Menu (
            item_id SERIAL PRIMARY KEY,
            name TEXT NOT NULL, category TEXT NOT NULL, price INTEGER NOT NULL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS Sales (
            order_id SERIAL PRIMARY KEY,
            item_name TEXT NOT NULL, quantity INTEGER NOT NULL,
            item_total INTEGER NOT NULL, timestamp TIMESTAMPTZ DEFAULT NOW())''')
        cursor.execute("SELECT COUNT(*) FROM Menu")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("INSERT INTO Menu (name, category, price) VALUES (%s, %s, %s)", [
                ('Masala Chai','Beverage',20),('Filter Coffee','Beverage',30),
                ('Cold Coffee','Beverage',80),('Mango Lassi','Beverage',60),
                ('Samosa','Snack',30),('Vada Pav','Snack',20),
                ('Paneer Tikka Sandwich','Snack',90),('Bun Maska','Snack',40),
                ('Gulab Jamun','Dessert',40),('Black Forest Pastry','Dessert',70)
            ])
        conn.commit()
        cursor.close()
        conn.close()

    def fetch_menu_data():
        conn = get_conn()
        df = pd.read_sql("SELECT * FROM Menu ORDER BY category, name", conn)
        conn.close()
        return df

    def fetch_sales_data():
        conn = get_conn()
        df = pd.read_sql("SELECT * FROM Sales ORDER BY timestamp DESC", conn)
        conn.close()
        df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_convert('Asia/Kolkata').dt.tz_localize(None)
        return df

    def record_transaction(cart_df):
        from datetime import datetime, timezone, timedelta
        IST = timezone(timedelta(hours=5, minutes=30))
        ist_time = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')
        conn = get_conn()
        cursor = conn.cursor()
        for _, row in cart_df.iterrows():
            cursor.execute(
                "INSERT INTO Sales (item_name, quantity, item_total, timestamp) VALUES (%s, %s, %s, %s)",
                (row['name'], int(row['quantity']), int(row['subtotal']), ist_time)
            )
        conn.commit()
        cursor.close()
        conn.close()

    def update_menu_item(item_id, new_name, new_price):
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("UPDATE Menu SET name=%s, price=%s WHERE item_id=%s", (new_name, new_price, item_id))
        conn.commit()
        cursor.close()
        conn.close()

    def add_menu_item(name, category, price):