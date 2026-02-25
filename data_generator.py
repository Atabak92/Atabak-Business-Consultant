import pandas as pd
import numpy as np
import random

# Set seed for reproducibility so the numbers don't jump around wildly
np.random.seed(42)

print("⏳ Generating realistic manufacturing data with a target profit margin (8% - 12%)...")

# --- 1. Product Definitions (25 Plastic Parts) ---
product_names = [
    "PVC Pipe 20mm", "PVC Pipe 50mm", "PE Water Tank 500L", "Plastic Pallet", "Nylon Gear",
    "Industrial Plastic Container", "Plastic Valve", "Cable Tie Pack", "Plastic Chair", "Plastic Table",
    "Car Bumper Part", "Dashboard Panel", "Medical Syringe Body", "Pet Bottle 1L", "Pet Bottle 500ml",
    "Plastic Crate", "Irrigation Dripper", "Greenhouse Film Roll", "Plastic Bucket 20L", "Safety Helmet",
    "Plastic Gearbox Housing", "Electrical Conduit", "Switch Box", "Plastic Hinge", "Custom Injection Mold"
]
product_ids = [f"PRD-{i:03d}" for i in range(1, 26)]
target_prices = np.random.uniform(5.0, 150.0, 25).round(2)

df_products = pd.DataFrame({
    "Product_ID": product_ids,
    "Product_Name": product_names,
    "Selling_Price": target_prices
})

# --- 2. Sales Invoices (Daily sales over 2025) ---
dates_2025 = pd.date_range(start="2025-01-01", end="2025-12-31")
sales_data = []
invoice_counter = 1001

for date in dates_2025:
    for _ in range(np.random.randint(2, 6)): # 2 to 5 invoices per day
        prod_idx = np.random.randint(0, 25)
        qty = np.random.randint(20, 500)
        price = target_prices[prod_idx]
        sales_data.append([
            date.strftime("%Y-%m-%d"), f"INV-{invoice_counter}", product_ids[prod_idx], 
            qty, price, round(qty * price, 2)
        ])
        invoice_counter += 1

df_sales = pd.DataFrame(sales_data, columns=["Date", "Invoice_ID", "Product_ID", "Quantity", "Unit_Price", "Total_Revenue"])

# Calculate total annual revenue to reverse-engineer the expenses
total_revenue = df_sales["Total_Revenue"].sum()

# --- 3. Reverse Engineering Expenses (The secret to realistic margins!) ---
# Target a strict profit margin between 8% and 12%
target_margin = np.random.uniform(0.08, 0.12)
target_profit = total_revenue * target_margin

# Calculate the exact total expenses needed to achieve this profit
total_expenses_needed = total_revenue - target_profit

# Distribute this total expense across 12 months and various categories
expense_categories = [
    "Raw Materials (PE, PP, PVC)", # Highest cost
    "Worker Salaries & Benefits", 
    "Logistics & Freight", 
    "Maintenance & Utilities", 
    "Taxes & Insurance", 
    "Cost of Capital"
]

# Weight of each category (e.g., raw materials take 50% of total expenses)
category_weights = [0.50, 0.20, 0.10, 0.08, 0.07, 0.05]

expenses_data = []
for month in range(1, 13):
    monthly_expense_pool = total_expenses_needed / 12
    # Add a slight 5% variance to make monthly expenses look natural, not flat
    monthly_expense_pool *= np.random.uniform(0.95, 1.05) 
    
    for i, exp in enumerate(expense_categories):
        # Allocate budget based on category weight
        amt = monthly_expense_pool * category_weights[i]
        expenses_data.append([f"2025-{month:02d}", exp, round(amt, 2)])

df_expenses = pd.DataFrame(expenses_data, columns=["Month", "Category", "Amount"])

# --- 4. Export to Excel ---
save_path = r"C:\Users\GCC\Downloads\New folder - Copy\Plastic_Manufacturing_Data_2025.xlsx"
with pd.ExcelWriter(save_path, engine='openpyxl') as writer:
    df_products.to_excel(writer, sheet_name="Products", index=False)
    df_sales.to_excel(writer, sheet_name="Sales_Invoices", index=False)
    # Merged all operational and material costs into one sheet for dashboard simplicity
    df_expenses.to_excel(writer, sheet_name="All_Expenses", index=False)

print("-" * 50)
print(f"✅ Data generated successfully!")
print(f"📊 Total Revenue: ${total_revenue:,.0f}")
print(f"📉 Total Expenses: ${total_expenses_needed:,.0f}")
print(f"💰 Engineered Profit Margin: {target_margin*100:.1f}%")
print("-" * 50)