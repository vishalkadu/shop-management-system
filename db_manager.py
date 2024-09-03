import sqlite3

class DBManager:
    def __init__(self, db_name='shop_data.db'):
        self.conn = sqlite3.connect(db_name)
        self.c = self.conn.cursor()
        self._init_db()

    def _init_db(self):
        self.c.execute('''CREATE TABLE IF NOT EXISTS products
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, product_name TEXT UNIQUE, price REAL)''')
        self.c.execute('''CREATE TABLE IF NOT EXISTS stock
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, date_added DATE, quantity INTEGER,
                         FOREIGN KEY (product_id) REFERENCES products(id))''')
        self.c.execute('''CREATE TABLE IF NOT EXISTS sales
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, date_of_sale DATE, quantity INTEGER, total REAL,
                         FOREIGN KEY (product_id) REFERENCES products(id))''')
        self.conn.commit()

    def close(self):
        self.conn.commit()
        self.conn.close()
