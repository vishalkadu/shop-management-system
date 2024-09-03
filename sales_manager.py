import base64
import tempfile
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from fpdf import FPDF

from data_exporter import DataExporter


class SalesManager:
    def __init__(self, cursor):
        self.c = cursor

    @staticmethod
    def generate_pdf_bill(date_of_sale, product_name, price, quantity, total, customer_name, customer_mobile):
        pdf = FPDF()
        pdf.add_page()

        # Set title font and color
        pdf.set_font("Arial", "B", 16)
        pdf.set_text_color(0, 0, 128)  # Dark blue
        pdf.cell(200, 10, txt="Sale Bill", ln=True, align='C')

        # Add a line break
        pdf.ln(10)

        # Add customer information
        pdf.set_font("Arial", "B", 12)
        pdf.set_text_color(0, 0, 0)  # Black
        pdf.cell(100, 10, txt="Customer Information", ln=True)

        pdf.set_font("Arial", "", 12)
        pdf.cell(100, 10, txt=f"Customer Name: {customer_name}")
        pdf.cell(100, 10, txt=f"Customer Mobile: {customer_mobile}")

        # Add a line break
        pdf.ln(10)

        # Add sale details
        pdf.set_font("Arial", "B", 12)
        pdf.cell(100, 10, txt="Sale Details", ln=True)

        pdf.set_font("Arial", "", 12)
        pdf.cell(100, 10, txt=f"Date of Sale: {date_of_sale}")
        pdf.ln(8)
        pdf.cell(100, 10, txt=f"Product Name: {product_name}")
        pdf.ln(8)
        pdf.cell(100, 10, txt=f"Price per Unit: ${price:.2f}")
        pdf.ln(8)
        pdf.cell(100, 10, txt=f"Quantity Sold: {quantity}")
        pdf.ln(8)
        pdf.cell(100, 10, txt=f"Total Amount: ${total:.2f}")

        # Add footer
        pdf.ln(20)
        pdf.set_font("Arial", "I", 10)
        pdf.set_text_color(128, 128, 128)  # Gray
        pdf.cell(200, 10, txt="Thank you for your purchase!", ln=True, align='C')

        # Save PDF to a temporary file and return the file path
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            pdf.output(tmp_file.name)
            return tmp_file.name  # Return the file path

    def record_sale(self):
        st.header("Record a Sale")
        try:
            stock_data = self.c.execute("SELECT product_name FROM products").fetchall()
            product_options = [item[0] for item in stock_data]

            product_name = st.selectbox("Product Name", product_options)
            if product_name:
                price = self.c.execute("SELECT price FROM products WHERE product_name=?", (product_name,)).fetchone()[0]
                quantity = st.number_input("Quantity Sold", min_value=1, format="%d")
                total = price * quantity

                # Capture customer information
                st.subheader("Customer Information")
                customer_name = st.text_input("Customer Name")
                customer_mobile = st.text_input("Customer Mobile")

                if st.button("Record Sale"):
                    try:
                        product_id = \
                        self.c.execute("SELECT id FROM products WHERE product_name=?", (product_name,)).fetchone()[0]
                        self.c.execute("UPDATE stock SET quantity = quantity - ? WHERE product_id = ?",
                                       (quantity, product_id))
                        date_of_sale = datetime.now().strftime("%Y-%m-%d")
                        self.c.execute(
                            "INSERT INTO sales (product_id, date_of_sale, quantity, total) VALUES (?, ?, ?, ?)",
                            (product_id, date_of_sale, quantity, total))
                        self.c.connection.commit()
                        st.success("Sale recorded successfully!")

                        st.subheader("Generated Bill")
                        st.write(f"**Date of Sale:** {date_of_sale}")
                        st.write(f"**Product Name:** {product_name}")
                        st.write(f"**Price per Unit:** ${price:.2f}")
                        st.write(f"**Quantity Sold:** {quantity}")
                        st.write(f"**Total Amount:** ${total:.2f}")

                        # Generate and download PDF bill
                        pdf_path = self.generate_pdf_bill(date_of_sale, product_name, price, quantity, total,
                                                          customer_name, customer_mobile)

                        # Encode PDF to base64 for embedding
                        with open(pdf_path, "rb") as f:
                            pdf_bytes = f.read()
                            b64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')

                        pdf_display = f'<embed src="data:application/pdf;base64,{b64_pdf}" width="600" height="800" type="application/pdf">'
                        st.markdown(pdf_display, unsafe_allow_html=True)

                        # Print button
                        print_button = f"""
                        <a href="data:application/octet-stream;base64,{b64_pdf}" download="bill.pdf" target="_blank">
                        <button>Print Bill</button>
                        </a>
                        """
                        st.markdown(print_button, unsafe_allow_html=True)

                    except Exception as e:
                        st.error(f"An error occurred while recording the sale: {e}")
        except Exception as e:
            st.error(f"An error occurred while fetching stock data for sale: {e}")

    def view_sales(self):
        st.header("Sales Records")
        try:
            sales_data = self.c.execute("""SELECT s.id, s.date_of_sale, p.product_name, p.price, s.quantity, s.total
                                          FROM sales s
                                          JOIN products p ON s.product_id = p.id""").fetchall()
            if sales_data:
                df = pd.DataFrame(sales_data, columns=["ID", "Date of Sale", "Product", "Price", "Quantity", "Total"])
                st.table(df)

                csv = DataExporter.export_to_csv(df, "sales_data.csv")
                st.download_button(label="Download Sales CSV", data=csv, file_name="sales_data.csv", mime="text/csv")
            else:
                st.write("No sales data available.")
        except Exception as e:
            st.error(f"An error occurred while fetching sales data: {e}")




    def show_sales_dashboard(self):
            st.header("Sales Dashboard")
            try:
                # Fetch data for dashboard
                total_sales = self.c.execute("SELECT SUM(total) FROM sales").fetchone()[0]
                num_sales = self.c.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
                most_sold_product = self.c.execute("""SELECT p.product_name, SUM(s.quantity) as total_quantity
                                                      FROM sales s
                                                      JOIN products p ON s.product_id = p.id
                                                      GROUP BY p.product_name
                                                      ORDER BY total_quantity DESC
                                                      LIMIT 1""").fetchone()

                if most_sold_product:
                    most_sold_product_name, most_sold_quantity = most_sold_product
                else:
                    most_sold_product_name, most_sold_quantity = "N/A", 0

                st.subheader("Total Sales")
                st.write(f"**Total Sales Amount:** ${total_sales:.2f}")

                st.subheader("Number of Sales")
                st.write(f"**Number of Sales:** {num_sales}")

                st.subheader("Most Sold Product")
                st.write(f"**Product Name:** {most_sold_product_name}")
                st.write(f"**Quantity Sold:** {most_sold_quantity}")

                # Create a graph for total sales over time
                st.subheader("Sales Over Time")
                sales_over_time = self.c.execute("""SELECT date_of_sale, SUM(total) as total_sales
                                                    FROM sales
                                                    GROUP BY date_of_sale
                                                    ORDER BY date_of_sale""").fetchall()
                df_sales_over_time = pd.DataFrame(sales_over_time, columns=["Date", "Total Sales"])
                fig_sales_over_time = go.Figure(data=[go.Scatter(x=df_sales_over_time["Date"],
                                                                 y=df_sales_over_time["Total Sales"],
                                                                 mode='lines+markers',
                                                                 name='Total Sales')])
                fig_sales_over_time.update_layout(title='Sales Over Time',
                                                  xaxis_title='Date',
                                                  yaxis_title='Total Sales',
                                                  xaxis=dict(tickformat='%Y-%m-%d'))
                st.plotly_chart(fig_sales_over_time)

                # Create a pie chart for sales by product
                st.subheader("Sales Distribution by Product")
                sales_by_product = self.c.execute("""SELECT p.product_name, SUM(s.total) as total_sales
                                                     FROM sales s
                                                     JOIN products p ON s.product_id = p.id
                                                     GROUP BY p.product_name""").fetchall()
                df_sales_by_product = pd.DataFrame(sales_by_product, columns=["Product Name", "Total Sales"])
                fig_sales_by_product = go.Figure(data=[go.Pie(labels=df_sales_by_product["Product Name"],
                                                              values=df_sales_by_product["Total Sales"],
                                                              hole=0.4)])
                fig_sales_by_product.update_layout(title='Sales Distribution by Product')
                st.plotly_chart(fig_sales_by_product)

            except Exception as e:
                st.error(f"An error occurred while generating the sales dashboard: {e}")

    def display(self):
        st.sidebar.header("Sales Manager")
        page = st.sidebar.selectbox("Select a page", ["Record Sale", "View Sales", "Sales Dashboard"])

        if page == "Record Sale":
            self.record_sale()
        elif page == "View Sales":
            self.view_sales()
        elif page == "Sales Dashboard":
            show_dashboard = st.sidebar.checkbox("Show Sales Dashboard", value=True)
            if show_dashboard:
                self.show_sales_dashboard()

