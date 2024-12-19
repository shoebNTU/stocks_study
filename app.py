import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

def nan_to_zero(x):
    if np.isnan(x):
        return 0.0
    else:
        return x
    
def is_valid_ticker(symbol):
    ticker = yf.Ticker(symbol)
    try:
        info = ticker.info
        # Check if the 'symbol' key exists in the info dictionary
        return 'symbol' in info and info['symbol'] == symbol
    except Exception as e:
        print(f"Error: {e}")
        return False
    
@st.cache_data
def load_data(file_path):
    data = pd.read_csv(file_path)
    data['Last Sale'] = data['Last Sale'].apply(lambda x: float(x.replace('$','')))
    return data

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

st.sidebar.title('Search Parameters')

name = st.sidebar.text_input('Please enter `Name` of the company',value='').lower().strip()
symbol = st.sidebar.text_input('Please enter `Ticker` of the company',value='').lower().strip()
sectors = ['Basic Materials', 'Consumer Discretionary', 'Consumer Staples',
       'Energy', 'Finance', 'Health Care', 'Industrials', 'Miscellaneous',
       'Real Estate', 'Technology', 'Telecommunications', 'Utilities', 'None']
sector_sel = st.sidebar.multiselect('Please select one or more sectors of interest', options=sectors, default=sectors)

# do you want to check for halal status?
halal_check = st.sidebar.selectbox(label='Do you want to check for Halal status?', options = ['Yes','No'], index=1)

# enter number of search terms
no_of_search = st.sidebar.number_input(label='Please enter `number` of `keywords` to be searched', value=1, min_value=0)
if no_of_search:
    search_text = []
    for i in range(no_of_search):
    # enter search term
        search_text.append(st.sidebar.text_input(label='Please enter `keyword` to be searched in `DESCRIPTION` column', value='', key=i).lower().strip())

    search_expr = ' & '.join([f"df.Description.astype(str).str.contains('{text}', case=False)"  for text in search_text]) # possible to change to OR


submit = st.sidebar.button('Submit')

with st.expander('Halal calculation'):
    st.info("""
- non_compliant_income = (Interest-Income/Total-Revenue) --> `<5%`
- Interest-bearing securities = (Cash + Cash Equivalents + Deposits) / Market Cap --> `<30%`
- Interest-bearing debt = Total debt / Market Cap --> `<30%`
"""
            
        )
if submit:
    # read dataframe
    df = load_data('small_micro_nano_halal_6.csv')
    df = df[df.Symbol.str.contains(symbol, case=False)]
    df.Sector = df.Sector.fillna('None')
    df = df[df.Sector.astype(str).str.contains('|'.join(sector_sel))]
    if len(df):
        df = df[df.Name.str.contains(name, case=False)]

        print(list(df.Sector.unique()))
        if no_of_search:
            df = df[eval(search_expr)] # filtering based on description
        if halal_check == 'Yes':
            df = df[(df.nc_income.astype(float) < 5) & \
                    (df.int_dep.astype(float) < 30) & (df.debt.astype(float) < 30)]

        df = df[['Symbol','Name', 'Country',
        'nc_income', 'int_dep', 'debt', 'Sector', 'Description','IPO Year', 'Industry']]
        
        df.reset_index(drop=True, inplace=True)
        st.success(f'Total number of rows found - {len(df)}')
        st.data_editor(df, use_container_width=True)
    else:
        st.error('Please check the ticker.')

with st.expander('Ticker Query for non-NASDAQ stocks'):
    st.info('Please enter ticker symbol to check for `HALAL` status')
    ticker_input = st.text_input(label='Please enter symbol. Refer https://finance.yahoo.com for correct ticker symbol.', value='').upper().strip()

    if ticker_input:
        get_status = st.button('Check')

        if get_status:
            if is_valid_ticker(ticker_input):
                nc_income, interest_bearing_securities, interest_bearing_debt = get_data(ticker_input)
                st.dataframe(pd.DataFrame({'nc_income':[nc_income],'interest_bearing_securities':[interest_bearing_securities], 
                            'interest_bearing_debt':[interest_bearing_debt]}))
                c1,_ = st.columns([1,4])
                with c1:
                    if (0 < nc_income < 5) and (0 < interest_bearing_securities < 30) and (0 < interest_bearing_debt < 30):
                        st.success('HALAL')
                    elif (nc_income < 5) and (interest_bearing_securities < 30) and (interest_bearing_debt < 30):
                        st.warning('Likely HALAL. Please check.')
                    else:
                        st.error('Non-HALAL')

            else:
                st.error('Please validate your ticker symbol at yahoo finance')
