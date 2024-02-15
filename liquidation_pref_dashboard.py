import streamlit as st
import pandas as pd
import numpy as np

# Load data
# Ensure you have the 'russell_2000.xlsx' file in the same directory as your Streamlit app
# or adjust the path accordingly
df = pd.read_excel("liq_pref_data.xlsx", sheet_name="Data")
df = df.dropna()
df = df[['Ticker', 'Market Cap', 'return_1y', 'return_5y']]

st.title('Liquidation Preference Premium')
st.subheader("Calculate the return premium on the Russell 2000")

# Controls
equity_stake_per_company = st.slider('Equity Stake per Company', 0.0, 1.0, 0.1)
liq_pref = st.slider('Liquidity Preference', 0.0, 3.0, 1.0)
participating = st.checkbox('Participating', False)

# Main logic
def calculate_liquidity_preferences(df, equity_stake_per_company, liq_pref, participating):
    # Old investment value = old market cap * equity stake investmed 
    # NOTE: We don't have the data about the old market cap so we assume it = new market cap / stock returns (assume # shares stays constant)
    df['original_investment_value_1y'] = df.apply(lambda row: (row['Market Cap'] / (1 + row['return_1y'])) * equity_stake_per_company,
                                    axis=1)


    df['original_investment_value_5y'] = df.apply(lambda row: (row['Market Cap'] / (1 + row['return_5y'])) * equity_stake_per_company,
                                  axis=1)


    if participating:
        # Receive MAX of 1) Your equity stake in the company OR 2) MIN(size of your liquidity preference + equity stake in remaining market cap, total market cap of company)
        df['new_equity_value_1y_liq_pref'] = df.apply(lambda row: max(equity_stake_per_company * row['Market Cap'],
                                            min(row['original_investment_value_1y'] * liq_pref + (row['Market Cap'] - row['original_investment_value_1y'] * liq_pref) * equity_stake_per_company, row['Market Cap'])), axis = 1)
        
        df['new_equity_value_5y_liq_pref'] = df.apply(lambda row: max(equity_stake_per_company * row['Market Cap'],
                                            min(row['original_investment_value_5y'] * liq_pref + (row['Market Cap'] - row['original_investment_value_5y'] * liq_pref) * equity_stake_per_company, row['Market Cap'])), axis = 1)
    else:
        # Receive MAX of 1) Your equity stake in the company OR 2) MIN(size of your liquidity preference, total market cap of company)
        df['new_equity_value_1y_liq_pref'] = df.apply(lambda row: max(equity_stake_per_company * row['Market Cap'],
                                                                min(row['original_investment_value_1y'] * liq_pref, row['Market Cap'])), axis=1)
        
        df['new_equity_value_5y_liq_pref'] = df.apply(lambda row: max(equity_stake_per_company * row['Market Cap'],
                                                                min(row['original_investment_value_5y'] * liq_pref, row['Market Cap'])), axis=1)

    df['return_1y_liq_pref'] = df['new_equity_value_1y_liq_pref'] / df['original_investment_value_1y']  - 1

    df['return_5y_liq_pref'] = (df['new_equity_value_5y_liq_pref'] / df['original_investment_value_5y'])**(1/5)  - 1

    return df

# Calculate the new equity value given a liquidity preference
df = calculate_liquidity_preferences(df, equity_stake_per_company, liq_pref, participating)

# Calculate the new equity value without a liquidity preference
df['new_equity_value_no_liq_pref'] = equity_stake_per_company * df['Market Cap']

# Calculate and display returns
total_market_cap = df['Market Cap'].sum()

# Formula; total return = (current value / old value)^(1/num years) - 1
total_return_1y = df['new_equity_value_no_liq_pref'].sum() / df['original_investment_value_1y'].sum() - 1
total_return_1y_liq_pref =  df['new_equity_value_1y_liq_pref'].sum() / df['original_investment_value_1y'].sum() - 1

total_return_5y = (df['new_equity_value_no_liq_pref'].sum() / df['original_investment_value_5y'].sum())**(1/5) - 1
total_return_5y_liq_pref = (df['new_equity_value_5y_liq_pref'].sum() / df['original_investment_value_5y'].sum())**(1/5) - 1

# Create a DataFrame to hold the data
data = {
    "Description": ["1Y Premium", "Total Return 1Y", "Total Return 1Y with Liquidity Preference","5Y Premium", "Total Return 5Y", "Total Return 5Y with Liquidity Preference"],
    "Value": [
        total_return_1y_liq_pref - total_return_1y, 
        total_return_1y, 
        total_return_1y_liq_pref,
        total_return_5y_liq_pref - total_return_5y, 
        total_return_5y, 
        total_return_5y_liq_pref
    ]
}

results_df = pd.DataFrame(data)


df = pd.DataFrame(data)

# Format numbers as percentages
df['Value'] = df['Value'].apply(lambda x: "{:.2%}".format(x))

# Custom HTML generation to remove header and index, and style specific rows
html_str = '<table>'
for i, row in df.iterrows():
    bg_color = 'background-color:#f0f0f5;' if "Premium" in row['Description'] else ''
    html_str += f'<tr style="{bg_color}"><td>{row["Description"]}</td><td>{row["Value"]}</td></tr>'
html_str += '</table>'

# Display the custom HTML table in Streamlit
st.markdown(html_str, unsafe_allow_html=True)
