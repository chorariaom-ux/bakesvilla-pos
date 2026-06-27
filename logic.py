import datetime
import pandas as pd
from database import fetch_menu_data, fetch_sales_data, record_transaction

def get_categorized_menu():
    menu_df = fetch_menu_data()
    categories = menu_df['category'].unique().tolist()
    return menu_df, categories

def process_checkout(cart_df: pd.DataFrame, discount: int) -> str:
    subtotal = cart_df['subtotal'].sum()
    grand_total = subtotal - discount
    record_transaction(cart_df)
    return generate_receipt_html(cart_df, subtotal, discount, grand_total)

def generate_receipt_html(cart_df, subtotal, discount, grand_total) -> str:
    current_time = datetime.datetime.now().strftime('%d-%b-%Y %I:%M %p')
    items_html = "".join(
        f"<tr><td>{row['name']}</td><td class='center'>{row['quantity']}</td><td class='right'>₹{row['subtotal']}</td></tr>"
        for _, row in cart_df.iterrows()
    )
    discount_html = ""
    if discount > 0:
        discount_html = f"<tr><td colspan='2' style='text-align:right;padding-top:5px;'>Discount:</td><td class='right' style='padding-top:5px;'>-₹{discount}</td></tr>"

    return f"""
    <html><head><style>
        body {{ font-family: 'Courier New', monospace; width: 300px; margin: auto; padding: 15px; color: black; }}
        .center {{ text-align: center; }} .right {{ text-align: right; }}
        .dashed {{ border-top: 1px dashed #000; margin: 10px 0; }}
        table {{ width: 100%; font-size: 14px; border-collapse: collapse; }}
        th {{ text-align: left; border-bottom: 1px solid #000; padding-bottom: 5px; }}
        .btn {{ width: 100%; padding: 12px; background-color: #4CAF50; color: white; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; margin-bottom: 15px; }}
        @media print {{ .btn {{ display: none; }} body {{ width: 100%; padding: 0; }} }}
    </style></head>
    <body>
        <button class="btn" onclick="window.print()">🖨️ PRINT BILL</button>
        <div class="center"><h2>BakesVilla</h2><p>Purnia, Bihar</p><p>{current_time}</p></div>
        <div class="dashed"></div>
        <table>
            <tr><th>Item</th><th class="center">Qty</th><th class="right">Amt</th></tr>
            {items_html}
        </table>
        <div class="dashed"></div>
        <table>
            <tr><td colspan='2' style='text-align:right;'>Subtotal:</td><td class='right'>₹{subtotal}</td></tr>
            {discount_html}
        </table>
        <h3 class="right">Total: ₹{grand_total}</h3>
        <div class="center"><p>*** Thank You ***</p></div>
    </body></html>
    """