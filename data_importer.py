import pandas as pd
import streamlit as st

class DataImporter:
    def __init__(self, cursor):
        self.c = cursor

    def import_from_csv(self, file):
        try:
            df = pd.read_csv(file)
            if all(col in df.columns for col in ["date_added", "product_name", "price", "quantity"]):
                # Import stock data
                for _, row in df.iterrows():
                    self.c.execute("INSERT OR IGNORE INTO products (product_name, price) VALUES (?, ?)",
                                   (row['product_name'], row['price']))
                    product_id = self.c.execute("SELECT id FROM products WHERE product_name=?", (row['product_name'],)).fetchone()[0]
                    self.c.execute("INSERT INTO stock (product_id, date_added, quantity) VALUES (?, ?, ?)",
                                   (product_id, row['date_added'], row['quantity']))
                st.success("Stock data imported successfully!")

            elif all(col in df.columns for col in ["date_of_sale", "product_name", "price", "quantity", "total"]):
                # Import sales data
                for _, row in df.iterrows():
                    self.c.execute("INSERT OR IGNORE INTO products (product_name, price) VALUES (?, ?)",
                                   (row['product_name'], row['price']))
                    product_id = self.c.execute("SELECT id FROM products WHERE product_name=?", (row['product_name'],)).fetchone()[0]
                    self.c.execute("INSERT INTO sales (product_id, date_of_sale, quantity, total) VALUES (?, ?, ?, ?)",
                                   (product_id, row['date_of_sale'], row['quantity'], row['total']))
                st.success("Sales data imported successfully!")

            else:
                st.error("CSV file does not match expected format.")

        except Exception as e:
            st.error(f"An error occurred while importing data: {e}")
