from datetime import datetime

import pandas as pd
import streamlit as st


class StockManager:
    def __init__(self, cursor):
        self.c = cursor

    def view_stock(self):
        st.header("Current Stock")

        query = """SELECT s.date_added, p.product_name, p.price, s.quantity
                   FROM stock s
                   JOIN products p ON s.product_id = p.id"""

        try:
            stock_data = self.c.execute(query).fetchall()
            if stock_data:
                df = pd.DataFrame(stock_data, columns=["Date Added", "Product", "Price", "Available Stock"])
                st.table(df)
            else:
                st.write("No stock data available.")
        except Exception as e:
            st.error(f"An error occurred while fetching stock data: {e}")

    def add_stock(self):
        st.header("Add or Update Stock Item")

        # Option to update existing item
        is_update = st.checkbox("Update existing item")

        if is_update:
            # Select an existing product to update
            existing_products = self.c.execute("SELECT product_name FROM products").fetchall()
            existing_product_names = [item[0] for item in existing_products]
            selected_product = st.selectbox("Select Product to Update", existing_product_names)

            if selected_product:
                # Fetch existing details
                product_details = self.c.execute(
                    "SELECT price FROM products WHERE product_name=?", (selected_product,)
                ).fetchone()
                product_name = selected_product
                price = st.number_input("Price", value=product_details[0], min_value=0.0, format="%.2f")
                quantity = st.number_input("Quantity to Add", min_value=0, format="%d")

                if st.button("Update Stock"):
                    try:
                        product_id = self.c.execute(
                            "SELECT id FROM products WHERE product_name=?", (product_name,)
                        ).fetchone()[0]

                        # Update the product details
                        self.c.execute("UPDATE products SET price=? WHERE id=?", (price, product_id))
                        self.c.execute("UPDATE stock SET quantity=quantity + ? WHERE product_id=?",
                                       (quantity, product_id))
                        self.c.connection.commit()
                        st.success(f"Stock for '{product_name}' updated successfully!")
                    except Exception as e:
                        st.error(f"An error occurred while updating stock: {e}")
        else:
            # Adding new stock item
            product_name = st.text_input("Product Name")
            price = st.number_input("Price", min_value=0.0, format="%.2f")
            quantity = st.number_input("Quantity", min_value=0, format="%d")

            if st.button("Add to Stock"):
                try:
                    if product_name and price > 0 and quantity > 0:
                        self.c.execute("INSERT OR IGNORE INTO products (product_name, price) VALUES (?, ?)",
                                       (product_name, price))
                        product_id = self.c.execute(
                            "SELECT id FROM products WHERE product_name=?", (product_name,)
                        ).fetchone()[0]
                        date_added = datetime.now().strftime("%Y-%m-%d")
                        self.c.execute("INSERT INTO stock (product_id, date_added, quantity) VALUES (?, ?, ?)",
                                       (product_id, date_added, quantity))
                        self.c.connection.commit()
                        st.success("New stock item added successfully!")
                    else:
                        st.error("Please fill in all fields correctly.")
                except Exception as e:
                    st.error(f"An error occurred while adding stock: {e}")
