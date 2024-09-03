"""
Welcome to the Shop Management App!

This powerful tool is designed to streamline inventory and sales management for your business.
With a user-friendly interface and seamless integration with an SQLite database, the app allows you to:

Manage Inventory: Effortlessly track and update your product stock.
Record Sales: Keep a detailed record of all sales transactions.
Import Data: Easily import product and sales data from CSV files.
Generate Reports: Create comprehensive reports on sales and inventory.
View Sales History: Access a complete history of all sales.
Dashboard: Get insightful visualizations of your sales data with interactive graphs and charts.

``` Author: Coder Vishal [ YouTube: https://www.youtube.com/@codervishaal ] ```


"""
import streamlit as st

from data_importer import DataImporter
from db_manager import DBManager
from sales_manager import SalesManager
from stock_manager import StockManager


def main():
    db = DBManager()
    stock_manager = StockManager(db.c)
    sales_manager = SalesManager(db.c)
    data_importer = DataImporter(db.c)

    st.title("Shop Management App")
    st.sidebar.title("Navigation")

    # option = st.sidebar.selectbox(
    #     "Choose an option",
    #     ["📦 View Stock", "➕ Add Stock", "💸 Record Sale", "🛒 Shopping", "📈 Import Data"]
    # )

    option = st.sidebar.selectbox(
        "Choose an option",
        ["📦 View Stock", "➕ Add Stock", "🛒 Shopping", "📈 Import Data"]
    )

    # USER INTERACTION
    if option == "📦 View Stock":

        stock_manager.view_stock()
    elif option == "➕ Add Stock":

        stock_manager.add_stock()

    # elif option == "💸 Record Sale":
    #
    #     sales_manager.record_sale()

    elif option == "🛒 Shopping":
        sales_manager.display()
    elif option == "📈 Import Data":

        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        if uploaded_file is not None:
            data_importer.import_from_csv(uploaded_file)

    db.close()


if __name__ == "__main__":
    main()
