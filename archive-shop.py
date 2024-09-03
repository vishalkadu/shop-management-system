import io
import sqlite3
from datetime import datetime

import pandas as pd
import streamlit as st


# Initialize database connection with normalized schema
def init_db():
    conn = sqlite3.connect('shop_data.db')
    c = conn.cursor()

    # Create tables
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, product_name TEXT UNIQUE, price REAL)''')

    c.execute('''CREATE TABLE IF NOT EXISTS stock
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, date_added DATE, quantity INTEGER,
                 FOREIGN KEY (product_id) REFERENCES products(id))''')

    c.execute('''CREATE TABLE IF NOT EXISTS sales
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, date_of_sale DATE, quantity INTEGER, total REAL,
                 FOREIGN KEY (product_id) REFERENCES products(id))''')

    return conn, c


conn, c = init_db()


# Export DataFrame to CSV
def export_to_csv(df, filename):
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    return buffer.getvalue()


# Import Data from CSV
def import_from_csv(file):
    try:
        df = pd.read_csv(file)

        if all(col in df.columns for col in ["date_added", "product_name", "price", "quantity"]):
            # Import stock data
            for _, row in df.iterrows():
                c.execute("INSERT OR IGNORE INTO products (product_name, price) VALUES (?, ?)",
                          (row['product_name'], row['price']))
                product_id = \
                c.execute("SELECT id FROM products WHERE product_name=?", (row['product_name'],)).fetchone()[0]
                c.execute("INSERT INTO stock (product_id, date_added, quantity) VALUES (?, ?, ?)",
                          (product_id, row['date_added'], row['quantity']))
            conn.commit()
            st.success("Stock data imported successfully!")

        elif all(col in df.columns for col in ["date_of_sale", "product_name", "price", "quantity", "total"]):
            # Import sales data
            for _, row in df.iterrows():
                c.execute("INSERT OR IGNORE INTO products (product_name, price) VALUES (?, ?)",
                          (row['product_name'], row['price']))
                product_id = \
                c.execute("SELECT id FROM products WHERE product_name=?", (row['product_name'],)).fetchone()[0]
                c.execute("INSERT INTO sales (product_id, date_of_sale, quantity, total) VALUES (?, ?, ?, ?)",
                          (product_id, row['date_of_sale'], row['quantity'], row['total']))
            conn.commit()
            st.success("Sales data imported successfully!")

        else:
            st.error("CSV file does not match expected format.")

    except Exception as e:
        st.error(f"An error occurred while importing data: {e}")


# Function to view stock with search, filter, and export
def view_stock():
    st.header("Current Stock")

    # Search and filter options
    search_term = st.text_input("Search Product")
    start_date = st.date_input("Start Date")
    end_date = st.date_input("End Date", datetime.now())

    query = """SELECT s.date_added, p.product_name, p.price, s.quantity
               FROM stock s
               JOIN products p ON s.product_id = p.id
               WHERE s.date_added BETWEEN ? AND ?"""
    params = [start_date, end_date]

    if search_term:
        query += " AND p.product_name LIKE ?"
        params.append(f"%{search_term}%")

    try:
        stock_data = c.execute(query, params).fetchall()
        if stock_data:
            df = pd.DataFrame(stock_data, columns=["Date Added", "Product", "Price", "Available Stock"])
            st.table(df)

            # Export to CSV
            csv = export_to_csv(df, "stock_data.csv")
            st.download_button(label="Download CSV", data=csv, file_name="stock_data.csv", mime="text/csv")

            # Low inventory alert
            low_stock = df[df["Available Stock"] < 5]  # Example threshold
            if not low_stock.empty:
                st.warning("Low stock alert for the following products:")
                st.table(low_stock)
        else:
            st.write("No stock data available.")
    except Exception as e:
        st.error(f"An error occurred while fetching stock data: {e}")


# Function to add stock
def add_stock():
    st.header("Add New Stock Item")
    product_name = st.text_input("Product Name")
    price = st.number_input("Price", min_value=0.0, format="%.2f")
    quantity = st.number_input("Quantity", min_value=0, format="%d")

    if st.button("Add to Stock"):
        try:
            if product_name and price > 0 and quantity > 0:
                c.execute("INSERT OR IGNORE INTO products (product_name, price) VALUES (?, ?)",
                          (product_name, price))
                product_id = c.execute("SELECT id FROM products WHERE product_name=?", (product_name,)).fetchone()[0]
                date_added = datetime.now().strftime("%Y-%m-%d")
                c.execute("INSERT INTO stock (product_id, date_added, quantity) VALUES (?, ?, ?)",
                          (product_id, date_added, quantity))
                conn.commit()
                st.success("Stock item added successfully!")
            else:
                st.error("Please fill in all fields correctly.")
        except Exception as e:
            st.error(f"An error occurred while adding stock: {e}")


# Function to record a sale and generate a bill
def record_sale():
    st.header("Record a Sale")
    try:
        stock_data = c.execute("SELECT product_name FROM products").fetchall()
        product_options = [item[0] for item in stock_data]

        product_name = st.selectbox("Product Name", product_options)
        if product_name:
            price = c.execute("SELECT price FROM products WHERE product_name=?", (product_name,)).fetchone()[0]
            quantity = st.number_input("Quantity Sold", min_value=1, format="%d")
            total = price * quantity

            if st.button("Record Sale"):
                try:
                    product_id = c.execute("SELECT id FROM products WHERE product_name=?", (product_name,)).fetchone()[
                        0]
                    c.execute("UPDATE stock SET quantity = quantity - ? WHERE product_id = ?", (quantity, product_id))
                    date_of_sale = datetime.now().strftime("%Y-%m-%d")
                    c.execute("INSERT INTO sales (product_id, date_of_sale, quantity, total) VALUES (?, ?, ?, ?)",
                              (product_id, date_of_sale, quantity, total))
                    conn.commit()
                    st.success("Sale recorded successfully!")

                    # Generate Bill
                    st.subheader("Generated Bill")
                    st.write(f"**Date of Sale:** {date_of_sale}")
                    st.write(f"**Product Name:** {product_name}")
                    st.write(f"**Price per Unit:** ${price:.2f}")
                    st.write(f"**Quantity Sold:** {quantity}")
                    st.write(f"**Total Amount:** ${total:.2f}")

                except Exception as e:
                    st.error(f"An error occurred while recording the sale: {e}")
    except Exception as e:
        st.error(f"An error occurred while fetching stock data for sale: {e}")


# Function to view sales with export option
def view_sales():
    st.header("Sales Records")
    try:
        sales_data = c.execute("""SELECT s.id, s.date_of_sale, p.product_name, p.price, s.quantity, s.total
                                  FROM sales s
                                  JOIN products p ON s.product_id = p.id""").fetchall()
        if sales_data:
            df = pd.DataFrame(sales_data, columns=["ID", "Date of Sale", "Product", "Price", "Quantity", "Total"])
            st.table(df)

            # Export sales data to CSV
            csv = export_to_csv(df, "sales_data.csv")
            st.download_button(label="Download Sales CSV", data=csv, file_name="sales_data.csv", mime="text/csv")
        else:
            st.write("No sales data available.")
    except Exception as e:
        st.error(f"An error occurred while fetching sales data: {e}")


# Streamlit App
st.title("Shop Management App")

# Sidebar Navigation
st.sidebar.title("Navigation")
option = st.sidebar.selectbox("Choose an option",
                              ["View Stock", "Add Stock", "Record Sale", "View Sales", "Import Data"])

# Call functions based on user selection
if option == "View Stock":
    view_stock()
elif option == "Add Stock":
    add_stock()
elif option == "Record Sale":
    record_sale()
elif option == "View Sales":
    view_sales()
elif option == "Import Data":
    st.header("Import Data from CSV")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    if uploaded_file is not None:
        import_from_csv(uploaded_file)
