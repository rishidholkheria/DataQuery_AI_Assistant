  import sqlite3
  import random
  from datetime import datetime, timedelta

  # Connect to (or create) the SQLite database
  connection = sqlite3.connect("salesDummyData.db")
  cursor = connection.cursor()

  # Create the sales table
  cursor.execute("""
  CREATE TABLE IF NOT EXISTS sales (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      order_date TEXT,
      region TEXT,
      product_name TEXT,
      unit_price REAL,
      quantity_sold INTEGER,
      discount_percent REAL,
      profit REAL
  )
  """)

  # Sample data for generation
  regions = ['North', 'South', 'East', 'West']
  products = ['Laptop', 'Tablet', 'Smartphone', 'Headphones', 'Monitor', 'Keyboard', 'Mouse', 'Printer']

  # Generate 80 rows of data
  base_date = datetime.today() - timedelta(days=180)

  data = []
  for i in range(80):
      order_date = (base_date + timedelta(days=random.randint(0, 180))).strftime('%Y-%m-%d')
      region = random.choice(regions)
      product = random.choice(products)
      unit_price = round(random.uniform(50, 1000), 2)
      quantity = random.randint(1, 20)
      discount = round(random.uniform(0, 30), 2)
      
      total_price = unit_price * quantity
      discount_amount = total_price * (discount / 100)
      cost_price = total_price - discount_amount
      profit = round(cost_price * random.uniform(0.05, 0.25), 2)  # assume 5-25% profit margin

      data.append((order_date, region, product, unit_price, quantity, discount, profit))

  # Insert the data into the table using parameterized query
  cursor.executemany("""
  INSERT INTO sales (order_date, region, product_name, unit_price, quantity_sold, discount_percent, profit) 
  VALUES (?, ?, ?, ?, ?, ?, ?)
  """, data)

  # Commit and close connection
  connection.commit()
  connection.close()

  print("Database 'salesDummyData.db' created with 80 dummy records.")
