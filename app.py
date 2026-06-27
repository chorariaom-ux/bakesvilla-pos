import streamlit as st
import pandas as pd
import io
import streamlit.components.v1 as components

from database import setup_database, fetch_sales_data, add_menu_item, update_menu_item
from logic import get_categorized_menu, process_checkout

st.set_page_config(page_title="BakesVilla", page_icon="🥮", layout="wide")
setup_database()

# --- SESSION STATE ---
if 'cart' not in st.session_state:
    st.session_state.cart = []
if 'last_receipt' not in st.session_state:
    st.session_state.last_receipt = None
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False
if 'discount' not in st.session_state:
    st.session_state.discount = 0

def add_item(item_id, name, price):
    st.session_state.last_receipt = None
    for item in st.session_state.cart:
        if item['item_id'] == item_id:
            item['quantity'] += 1
            return
    st.session_state.cart.append({'item_id': item_id, 'name': name, 'price': price, 'quantity': 1})

def remove_item(item_id):
    for item in st.session_state.cart:
        if item['item_id'] == item_id:
            if item['quantity'] > 1:
                item['quantity'] -= 1
            else:
                st.session_state.cart.remove(item)
            return

# --- SIDEBAR: ADMIN PANEL ---
with st.sidebar:
    st.header("⚙️ Admin Panel")

    if not st.session_state.admin_logged_in:
        st.info("Enter PIN to access Admin features.")
        pin = st.text_input("Admin PIN", type="password", key="pin_input")
        if st.button("Login", use_container_width=True):
            if pin == "1234":
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("Incorrect PIN")

    else:
        if st.button("Logout", use_container_width=True):
            st.session_state.admin_logged_in = False
            st.rerun()

        # --- UPDATE MENU ITEM ---
        st.markdown("---")
        st.subheader("📝 Update Menu Item")
        menu_df, _ = get_categorized_menu()
        item_names = menu_df['name'].tolist()

        selected_item = st.selectbox("Select Item to Edit", item_names, key="edit_select")
        if selected_item:
            item_row = menu_df[menu_df['name'] == selected_item].iloc[0]
            new_name = st.text_input("New Name", value=item_row['name'], key="edit_name")
            new_price = st.number_input("New Price (₹)", min_value=1, value=int(item_row['price']), key="edit_price")
            if st.button("💾 Save Changes", use_container_width=True):
                if new_name.strip() == "":
                    st.error("Name cannot be empty.")
                else:
                    update_menu_item(int(item_row['item_id']), new_name.strip(), new_price)
                    st.success(f"✅ '{selected_item}' updated!")
                    st.rerun()

        # --- ADD NEW ITEM ---
        st.markdown("---")
        st.subheader("➕ Add New Item")
        with st.expander("Add Item"):
            add_name = st.text_input("Item Name", key="add_name")
            add_cat = st.selectbox("Category", ["Beverage", "Snack", "Dessert", "Add-on"], key="add_cat")
            add_price = st.number_input("Price (₹)", min_value=1, value=50, key="add_price")
            if st.button("Add to Menu", use_container_width=True):
                if add_name.strip() == "":
                    st.error("Item name cannot be empty.")
                else:
                    add_menu_item(add_name.strip(), add_cat, add_price)
                    st.success(f"✅ '{add_name}' added!")
                    st.rerun()

        # --- FINANCIALS ---
        st.markdown("---")
        st.subheader("📊 Financials")
        sales_df = fetch_sales_data()

        if not sales_df.empty:
            sales_df['date'] = pd.to_datetime(sales_df['timestamp']).dt.date
            all_dates = sorted(sales_df['date'].unique(), reverse=True)

            filter_mode = st.radio("View", ["All Time", "By Date", "Date Range"], key="fin_filter")

            if filter_mode == "All Time":
                filtered_df = sales_df

            elif filter_mode == "By Date":
                selected_date = st.selectbox("Select Date", all_dates, key="fin_date")
                filtered_df = sales_df[sales_df['date'] == selected_date]

            elif filter_mode == "Date Range":
                col_from, col_to = st.columns(2)
                date_from = col_from.date_input("From", value=all_dates[-1], key="fin_from")
                date_to = col_to.date_input("To", value=all_dates[0], key="fin_to")
                filtered_df = sales_df[
                    (sales_df['date'] >= date_from) &
                    (sales_df['date'] <= date_to)
                ]

            # Revenue summary metrics
            st.markdown("---")
            total_revenue = filtered_df['item_total'].sum()
            total_orders = filtered_df['order_id'].nunique()
            total_items = filtered_df['quantity'].sum()

            m1, m2 = st.columns(2)
            m1.metric("💰 Revenue", f"₹{total_revenue}")
            m2.metric("🧾 Orders", total_orders)
            st.metric("📦 Items Sold", total_items)

            # Daily breakdown
            if filter_mode in ["All Time", "Date Range"]:
                st.markdown("**Daily Breakdown**")
                daily = filtered_df.groupby('date').agg(
                    Revenue=('item_total', 'sum'),
                    Orders=('order_id', 'nunique'),
                    Items=('quantity', 'sum')
                ).reset_index().sort_values('date', ascending=False)
                daily['Revenue'] = daily['Revenue'].apply(lambda x: f"₹{x}")
                st.dataframe(daily, use_container_width=True, hide_index=True)

            # Top selling items
            st.markdown("**Top Items**")
            top_items = filtered_df.groupby('item_name').agg(
                Qty=('quantity', 'sum'),
                Revenue=('item_total', 'sum')
            ).reset_index().sort_values('Qty', ascending=False).head(5)
            top_items['Revenue'] = top_items['Revenue'].apply(lambda x: f"₹{x}")
            top_items.columns = ['Item', 'Qty', 'Revenue']
            st.dataframe(top_items, use_container_width=True, hide_index=True)

            # Excel download
            st.markdown("---")
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                filtered_df.to_excel(writer, index=False, sheet_name='Sales')
                if filter_mode in ["All Time", "Date Range"]:
                    daily.to_excel(writer, index=False, sheet_name='Daily Summary')
                top_items.to_excel(writer, index=False, sheet_name='Top Items')
            st.download_button("📥 Download Excel", data=buffer,
                               file_name="BakesVilla_Sales.xlsx", use_container_width=True)
        else:
            st.info("No sales recorded yet.")

# --- MAIN DASHBOARD ---
st.title("🥮 BakesVilla")
st.markdown("---")
col_menu, _, col_cart = st.columns([6, 0.5, 3.5])

with col_menu:
    st.subheader("📋 Menu")
    menu_df, categories = get_categorized_menu()
    tabs = st.tabs(categories)

    for i, category in enumerate(categories):
        with tabs[i]:
            cat_items = menu_df[menu_df['category'] == category]
            grid_cols = st.columns(3)
            for index, row in cat_items.reset_index(drop=True).iterrows():
                with grid_cols[index % 3]:
                    if st.button(
                        f"➕ {row['name']}\n₹{row['price']}",
                        key=f"btn_{row['item_id']}",
                        use_container_width=True
                    ):
                        add_item(row['item_id'], row['name'], row['price'])
                        st.rerun()

with col_cart:
    st.subheader("🛒 Current Order")

    if st.session_state.last_receipt:
        st.success("✅ Order Complete!")
        components.html(st.session_state.last_receipt, height=500, scrolling=True)
        if st.button("⬅️ New Order", type="primary", use_container_width=True):
            st.session_state.last_receipt = None
            st.session_state.discount = 0
            st.rerun()

    elif len(st.session_state.cart) > 0:
        cart_df = pd.DataFrame(st.session_state.cart)
        cart_df['subtotal'] = cart_df['price'] * cart_df['quantity']
        raw_total = int(cart_df['subtotal'].sum())

        for _, row in cart_df.iterrows():
            c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
            c1.write(f"**{row['name']}**")
            c2.write(f"₹{int(row['price'])} x {int(row['quantity'])}")
            c3.write(f"**₹{int(row['subtotal'])}**")
            if c4.button("❌", key=f"del_{row['item_id']}"):
                remove_item(row['item_id'])
                st.rerun()

        st.markdown("---")

        # --- DISCOUNT FEATURE (% only) ---
        st.markdown("**Apply Discount**")
        discount_pct = st.number_input("Discount (%)", min_value=0, max_value=100, value=0, step=5, key="disc_pct")
        discount_amount = int(raw_total * discount_pct / 100)
        if discount_pct > 0:
            st.caption(f"Saving ₹{discount_amount} ({discount_pct}% off)")

        grand_total = raw_total - discount_amount

        st.markdown("---")
        col_sub, col_disc, col_total = st.columns(3)
        col_sub.metric("Subtotal", f"₹{raw_total}")
        col_disc.metric("Discount", f"-₹{discount_amount}")
        col_total.metric("Total", f"₹{grand_total}")
        st.markdown("---")

        a1, a2 = st.columns(2)
        if a1.button("🗑️ Clear", use_container_width=True):
            st.session_state.cart = []
            st.session_state.discount = 0
            st.rerun()
        if a2.button("💳 Checkout", type="primary", use_container_width=True):
            st.session_state.last_receipt = process_checkout(cart_df, discount_amount)
            st.session_state.cart = []
            st.session_state.discount = 0
            st.rerun()
    else:
        st.info("🛒 Cart is empty. Add items from the menu.")