import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

def nan_to_zero(x):
    if np.isnan(x):
        return 0.0
    else:
        return x

def get_data(ticker_in):

    try:
        ticker = yf.Ticker(ticker_in)

        qtr_st_index = ticker.quarterly_income_stmt.index
        if 'Total Revenue' in qtr_st_index:
            total_income = ticker.quarterly_income_stmt.loc['Total Revenue'].iloc[:4].sum()
        else:
            total_income = 0.0
        
        if 'Interest Income' in qtr_st_index: 
            non_compliant_income = ticker.quarterly_income_stmt.loc['Interest Income'].iloc[:4].sum()
        else:
            non_compliant_income = 0.0

        # total_cash = ticker.info['totalCash']
        if 'Cash And Cash Equivalents' in ticker.quarterly_balance_sheet.index:
            total_cash = ticker.quarterly_balance_sheet.loc['Cash And Cash Equivalents'].iloc[0]#.sum()
        else:
            total_cash = 0.0
            
        total_debt = ticker.info.get('totalDebt',0.0)
        market_cap = ticker.info.get('marketCap',0.0)

        if total_income > 0:
            non_compliant_ratio = non_compliant_income/total_income
        elif non_compliant_income > 0:
            non_compliant_ratio = 1.0 
        else:
            non_compliant_ratio = 0.0
                    
        if market_cap > 0:
            return [100*non_compliant_ratio, 100*total_cash/market_cap, 100*total_debt/market_cap]
        else:
            return [100*non_compliant_ratio, 0.0, 0.0]
    
    
    except Exception:
        print(f'Not found {ticker_in}')
        return [np.nan]*3

st.set_page_config(layout="wide")
st.title('Stock search')

# read dataframe
df = pd.read_csv('small_micro_nano_halal_6.csv')

st.sidebar.title('Parameters')
# enter number of search terms
no_of_search = st.sidebar.number_input(label='Please enter `number` of `keywords` to be searched', value=1, min_value=0)

if no_of_search:
    search_text = []
    for i in range(no_of_search):
    # enter search term
        search_text.append(st.sidebar.text_input(label='Please enter `keyword` to be searched in `DESCRIPTION` column', value='', key=i).lower().strip())

    search_expr = ' & '.join([f"df.Description.astype(str).str.contains('{text}', case=False)"  for text in search_text]) # possible to change to OR

    df = df[eval(search_expr)] # filtering based on description

    # do you want to check for halal status?
    halal_check = st.sidebar.selectbox(label='Do you want to check for Halal status?', options = ['Yes','No'])

    if halal_check == 'Yes':
         df = df[(df.nc_income.astype(float) < 5) & \
                (df.int_dep.astype(float) < 30) & (df.debt.astype(float) < 30)]

submit = st.sidebar.button('Submit')

with st.expander('Halal calculation'):
    st.info("""
- non_compliant_income = (Interest-Income/Total-Revenue) --> `<5%`
- Interest-bearing securities = (Cash + Cash Equivalents + Deposits) / Market Cap --> `<30%`
- Interest-bearing debt = Total debt / Market Cap --> `<30%`
"""
            
        )
if submit:
    df = df[['Symbol','Country', 
       'nc_income', 'int_dep', 'debt', 'Sector', 'Description','IPO Year', 'Industry',]]
    df.reset_index(drop=True, inplace=True)
    st.success(f'Total number of rows found - {len(df)}')
    st.write(df)
