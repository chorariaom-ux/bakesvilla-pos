import pandas as pd
from sqlalchemy import create_engine, text
import streamlit as st

DATABASE_URL = st.secrets["DATABASE_URL"].replace(
    "postgresql://", "postgresql+psycopg2://"
)
ENGINE = create_engine(DATABASE_URL, connect_args={"sslmode": "require"})

def setup_database():
    with ENGINE.connect() as conn:
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS Menu (
                item_id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price INTEGER NOT NULL
            )
        '''))
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS Sales (
                order_id SERIAL PRIMARY KEY,
                item_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                item_total INTEGER NOT NULL,
                timestamp TIMESTAMPTZ DEFAULT NOW()
            )
        '''))
        result = conn.execute(text("SELECT COUNT(*) FROM Menu")).scalar()
        if result == 0:
            conn.execute(text('''
                INSERT INTO Menu (name, category, price) VALUES
                (:a,:b,:c)
            '''), [
                {"a":"Masala Chai","b":"Beverage","c":20},
                {"a":"Filter Coffee","b":"Beverage","c":30},
                {"a":"Cold Coffee","b":"Beverage","c":80},
                {"a":"Mango Lassi","b":"Beverage","c":60},
                {"a":"Samosa","b":"Snack","c":30},
                {"a":"Vada Pav","b":"Snack","c":20},
                {"a":"Paneer Tikka Sandwich","b":"Snack","c":90},
                {"a":"Bun Maska","b":"Snack","c":40},
                {"a":"Gulab Jamun","b":"Dessert","c":40},
                {"a":"Black Forest Pastry","b":"Dessert","c":70}
            ])
        conn.commit()

def fetch_menu_data() -> pd.DataFrame:
    with ENGINE.connect() as conn:
        return pd.read_sql("SELECT * FROM Menu ORDER BY category, name", conn)

def fetch_sales_data() -> pd.DataFrame:
    with ENGINE.connect() as conn:
        return pd.read_sql("SELECT * FROM Sales ORDER BY timestamp DESC", conn)

def record_transaction(cart_df: pd.DataFrame):
    with ENGINE.connect() as conn:
        for _, row in cart_df.iterrows():
            conn.execute(text(
                "INSERT INTO Sales (item_name, quantity, item_total) VALUES (:name, :qty, :total)"
            ), {"name": row['name'], "qty": int(row['quantity']), "total": int(row['subtotal'])})
        conn.commit()

def update_menu_item(item_id: int, new_name: str, new_price: int):
    with ENGINE.connect() as conn:
        conn.execute(text(
            "UPDATE Menu SET name=:name, price=:price WHERE item_id=:id"
        ), {"name": new_name, "price": new_price, "id": item_id})
        conn.commit()

def add_menu_item(name: str, category: str, price: int):
    with ENGINE.connect() as conn:
        conn.execute(text(
            "INSERT INTO Menu (name, category, price) VALUES (:name, :cat, :price)"
        ), {"name": name, "cat": category, "price": price})
        conn.commit()

def delete_menu_item(item_id: int):
    with ENGINE.connect() as conn:
        conn.execute(text("DELETE FROM Menu WHERE item_id=:id"), {"id": item_id})
        conn.commit()