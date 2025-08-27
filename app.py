from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import os 
import sqlite3
import re
import pandas as pd

import google.generativeai as genai

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_sql_queries(question, prompt):
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content([prompt[0], question])
    
    sql_query = response.text.strip()
    sql_query = re.sub(r'^```sql\s*', '', sql_query, flags=re.IGNORECASE)
    sql_query = re.sub(r'^```\s*', '', sql_query)
    sql_query = re.sub(r'```\s*$', '', sql_query)
    sql_query = sql_query.strip()
    
    return sql_query

def debug_date_data(db):
    """Debug function to check date ranges in the database"""
    try:
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        
        # Check date range
        cur.execute("SELECT MIN(order_date) as min_date, MAX(order_date) as max_date, COUNT(*) as total_records FROM sales")
        date_info = cur.fetchone()
        
        # Check specific dates
        cur.execute("SELECT order_date, COUNT(*) FROM sales WHERE order_date < '2025-02-15' GROUP BY order_date ORDER BY order_date")
        before_feb_15 = cur.fetchall()
        
        # Check July records
        cur.execute("SELECT order_date, profit FROM sales WHERE strftime('%m', order_date) = '07' ORDER BY order_date")
        july_records = cur.fetchall()
        
        conn.close()
        
        return date_info, before_feb_15, july_records
    except Exception as e:
        return None, None, None
def read_sql_queries(sql, db):
    try:
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        
        # Get column names
        columns = [description[0] for description in cur.description]
        
        conn.close()
        return rows, columns
    except Exception as e:
        st.error(f"Error executing SQL query: {e}")
        return [], []

# CORRECTED PROMPT - Now correctly references the 'sales' table
prompt = [
    """
    You are an expert in converting English questions to SQL Query!
    The SQL database has a table named 'sales' and has the following columns - id, order_date, region, product_name, unit_price, quantity_sold, discount_percent, profit 
    
    The order_date column stores dates in 'YYYY-MM-DD' format (e.g., '2025-01-15', '2025-07-20').

    For example:
    Example 1 - "Show all records from north region" 
    SQL: SELECT * FROM sales WHERE region = 'North';
    
    Example 2 - "How many records are in north region?"
    SQL: SELECT COUNT(*) FROM sales WHERE region = 'North';
    
    Example 3 - "What is the total profit by region?"
    SQL: SELECT region, SUM(profit) as total_profit FROM sales GROUP BY region;
    
    Example 4 - "Show top 10 most profitable orders"
    SQL: SELECT * FROM sales ORDER BY profit DESC LIMIT 10;
    
    Example 5 - "List all smartphone sales"
    SQL: SELECT * FROM sales WHERE product_name = 'Smartphone';
    
    Example 6 - "How much total profit before 2025-02-15?"
    SQL: SELECT SUM(profit) as total_profit FROM sales WHERE order_date < '2025-02-15';
    
    Example 7 - "How much total profit in month of July?"
    SQL: SELECT SUM(profit) as total_profit FROM sales WHERE strftime('%m', order_date) = '07';
    
    Example 8 - "Show sales in January 2025"
    SQL: SELECT * FROM sales WHERE strftime('%Y-%m', order_date) = '2025-01';
    
    Example 9 - "Total profit by month"
    SQL: SELECT strftime('%Y-%m', order_date) as month, SUM(profit) as total_profit FROM sales GROUP BY strftime('%Y-%m', order_date) ORDER BY month;

    Important notes for DATE queries:
    - Use strftime() function for extracting parts of dates
    - For specific month: strftime('%m', order_date) = '07' (July)
    - For year-month: strftime('%Y-%m', order_date) = '2025-01'
    - For year: strftime('%Y', order_date) = '2025'
    - For day: strftime('%d', order_date) = '15'
    - Always use two-digit format for months: '01', '02', '07', '12'
    
    General notes:
    - Table name is 'sales' (lowercase)
    - Use single quotes for string values in SQL
    - When user asks to "show", "display", "list" records, use SELECT * to return all columns
    - When user asks "how many", "count", use COUNT(*) 
    - When user asks for "total profit", "sum of profit", use SUM(profit)
    - When user asks for "all records", "all data", always use SELECT * not COUNT(*)
    - Return only the SQL query without any markdown formatting
    - Do not include ```sql or ``` in your response
    - Column names are case-sensitive: id, order_date, region, product_name, unit_price, quantity_sold, discount_percent, profit
    
    Remember: 
    - "Show all records" = SELECT * (not COUNT)
    - "How many records" = SELECT COUNT(*)
    - "List all" = SELECT * (not COUNT)
    - "Display records" = SELECT * (not COUNT)
    - For date-based queries, always use strftime() for month/year extraction
"""
]

def load_all_sales_data(db):
    try:
        conn = sqlite3.connect(db)
        df = pd.read_sql_query("SELECT * FROM sales ORDER BY order_date DESC", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

# Streamlit app
st.set_page_config(page_title="SQL Query Generator with Gemini", layout="wide")
st.header("🔍 Data Query Assistant to Retrieve SQL Data")
st.subheader("Ask questions about your sales data in natural language!")

# Create tabs
tab1, tab2 = st.tabs(["🤖 AI Query", "📊 View All Data"])

with tab2:
    st.header("📊 Complete Sales Data")
    
    # Load and display all data
    all_data = load_all_sales_data("salesDummyData.db")
    
    if not all_data.empty:
        # Display summary statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Records", len(all_data))
        with col2:
            st.metric("Total Profit", f"${all_data['profit'].sum():,.2f}")
        with col3:
            st.metric("Average Order Value", f"${(all_data['unit_price'] * all_data['quantity_sold']).mean():,.2f}")
        with col4:
            st.metric("Products", all_data['product_name'].nunique())
        
        # Add filters
        st.subheader("🔍 Filter Data")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            selected_regions = st.multiselect(
                "Select Region(s)", 
                options=all_data['region'].unique(),
                default=all_data['region'].unique()
            )
        
        with col2:
            selected_products = st.multiselect(
                "Select Product(s)", 
                options=all_data['product_name'].unique(),
                default=all_data['product_name'].unique()
            )
        
        with col3:
            profit_range = st.slider(
                "Profit Range", 
                min_value=float(all_data['profit'].min()),
                max_value=float(all_data['profit'].max()),
                value=(float(all_data['profit'].min()), float(all_data['profit'].max()))
            )
        
        # Apply filters
        filtered_data = all_data[
            (all_data['region'].isin(selected_regions)) &
            (all_data['product_name'].isin(selected_products)) &
            (all_data['profit'] >= profit_range[0]) &
            (all_data['profit'] <= profit_range[1])
        ]
        
        st.subheader(f"Filtered Results ({len(filtered_data)} records)")
        st.dataframe(filtered_data, use_container_width=True)
        
        csv_all = filtered_data.to_csv(index=False)
        st.download_button(
            label="📥 Download Filtered Data as CSV",
            data=csv_all,
            file_name="sales_data_filtered.csv",
            mime="text/csv"
        )
        
        # Quick insights
        if not filtered_data.empty:
            st.subheader("📈 Quick Insights")
            col1, col2 = st.columns(2)
            
            with col1:
                top_products = filtered_data.groupby('product_name')['profit'].sum().sort_values(ascending=False).head(5)
                st.write("**Top 5 Products by Total Profit:**")
                for product, profit in top_products.items():
                    st.write(f"• {product}: ${profit:,.2f}")
            
            with col2:
                region_sales = filtered_data.groupby('region')['profit'].sum().sort_values(ascending=False)
                st.write("**Total Profit by Region:**")
                for region, profit in region_sales.items():
                    st.write(f"• {region}: ${profit:,.2f}")

with tab1:
    st.sidebar.header("📝 Example Questions")
    st.sidebar.write("• Show all records from North region")
    st.sidebar.write("• What is the total profit by region?")
    st.sidebar.write("• Which product has the highest unit price?")
    st.sidebar.write("• Show orders with discount more than 20%")
    st.sidebar.write("• What is the average quantity sold per product?")
    st.sidebar.write("• Show top 5 most profitable orders")
    st.sidebar.write("• How many orders were placed in each region?")
    st.sidebar.write("• How much total profit before 2025-02-15?")
    st.sidebar.write("• How much total profit in month of July?")
    st.sidebar.write("• Show all sales in January 2025")

    question = st.text_input("Input your question:", key="input", placeholder="e.g., Show me all smartphone sales")
    submit = st.button("Ask Question")

    if submit:
        if question:
            with st.spinner("Generating SQL query..."):
                sql_query = get_sql_queries(question, prompt)
                
            st.subheader("Generated SQL Query:")
            st.code(sql_query, language="sql")
            
            with st.spinner("Executing query..."):
                data, columns = read_sql_queries(sql_query, "salesDummyData.db")
            
            if data:
                st.subheader(f"Results ({len(data)} rows):")
                
                df = pd.DataFrame(data, columns=columns)
                st.dataframe(df, use_container_width=True)
                
                if len(data) > 0:
                    st.subheader("📊 Quick Stats:")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Total Rows", len(data))
                    
                    if 'profit' in columns:
                        profit_idx = columns.index('profit')
                        profits = [row[profit_idx] for row in data if isinstance(row[profit_idx], (int, float))]
                        
                        if profits:
                            with col2:
                                st.metric("Total Profit", f"${sum(profits):,.2f}")
                            with col3:
                                st.metric("Avg Profit", f"${sum(profits)/len(profits):,.2f}")
                
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download results as CSV",
                    data=csv,
                    file_name="query_results.csv",
                    mime="text/csv"
                )
            else:
                st.info("No results found or there was an error executing the query.")
        else:
            st.warning("Please enter a question first!")

st.markdown("---")
st.markdown("*Powered by Google Gemini AI*")