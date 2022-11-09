import pandas as pd
import json
import math
from datetime import datetime
import time
import logging
from kiteconnect import KiteConnect import pandas as pd
import json
import math
from datetime import datetime
import time
import logging
from kiteconnect import KiteConnect 
import os

# KITE CREDENTIALS


ZERODHA_API_KEY = open("D:\\GIST ALGOS\\INTRADAY EXPIRY ALGO\\order_access\\api_key.txt",'r').read()
ZERODHA_API_SECRET = open("D:\\GIST ALGOS\\INTRADAY EXPIRY ALGO\\order_access\\api_secret.txt",'r').read()
kite = KiteConnect(api_key=ZERODHA_API_KEY)

access_token ='oq0OUMgYUpyqfLDVVg5FJQH2xkdWLqUk'
kite.set_access_token(access_token)

#kite = KiteConnect(api_key="crriyu5vlpm08iua")
# print(kite.login_url())
# data = kite.generate_session('UR2HIYCOqqY5PdsljoCcUe8qAyOeGfp8', api_secret="r91a37hxsacj8fxxfgoyn5per201pkvk")
# print(data['access_token'])


# ALGO PARAMETERS
name_idx='NIFTY'
scrip='NSE:NIFTY 50'
symbol="NIFTY10NOV"
expiry_date='2022/11/10'#yyyy/mm/dd
expiry_date_option ='2022-11-10'#yyyy-mm-dd
strike_scale=50# for nifty.. change it to 25 for bank nifty
refresh_time =60#seconds
india_vix=kite.ltp("NSE:INDIA VIX")['NSE:INDIA VIX']['last_price']
# SAMCO CREDENTIALS FOR OPTION CHAIN -- NEED TO SHIFT WITH RESPECTIVE PLATFORM
def run_credentials():
    from snapi_py_client.snapi_bridge import StocknoteAPIPythonBridge
    samco = StocknoteAPIPythonBridge()
    login = samco.login(
        body={"userId": 'PK1197', 'password': 'alpha@12345', 'yob': '1983'})
    token = json.loads(login)['sessionToken']
    headers = {
        'Accept': 'application/json',
        'x-session-token': token,
        'login':login,
        'samco':samco
    }
    return(headers)

# ZERODHA ENTERING TRADES
def enter_position(symbolname):
    print(symbolname)
    order_id=0
    try:
        order_id = kite.place_order(tradingsymbol=symbolname,
                                exchange=kite.EXCHANGE_NFO,
                                transaction_type=kite.TRANSACTION_TYPE_SELL,
                                quantity=50,
                                variety=kite.VARIETY_REGULAR,
                                order_type=kite.ORDER_TYPE_MARKET,
                                product=kite.PRODUCT_NRML,
                                validity=kite.VALIDITY_DAY)
        logging.info("Order placed. ID is: {}".format(order_id))
        print('order id is',order_id)
    except Exception as e:
        print(e)
        logging.info("Order placement failed: {}".format(e))
        order_id=0
        print('order id is',order_id)
    return order_id

# ZERODHA CLOSING TRADES AS PER ADJUSTMENTS
def close_position(symbolname):
    order_id=0
    try:
        order_id = kite.place_order(tradingsymbol=symbolname,
                                exchange=kite.EXCHANGE_NFO,
                                transaction_type=kite.TRANSACTION_TYPE_BUY,
                                quantity=50,
                                variety=kite.VARIETY_REGULAR,
                                order_type=kite.ORDER_TYPE_MARKET,
                                product=kite.PRODUCT_NRML,
                                validity=kite.VALIDITY_DAY)

        logging.info("Order placed. ID is: {}".format(order_id))
        print('order id is',order_id)
    except Exception as e:
        logging.info("Order placement failed: {}".format(e))
        order_id=0
        print('order id is',order_id)
    return order_id

# INITIATING SAMCO PROCESS TO GET OPTION CHAIN
creds=run_credentials()
creds['samco'].set_session_token(sessionToken=creds['x-session-token'])
samco=creds['samco']
#option_strikes =json.loads(samco.search_equity_derivative(search_symbol_name=symbol,exchange=samco.EXCHANGE_NFO))
#current_price =samco.get_quote(symbol_name='NIFTY',exchange=samco.EXCHANGE_NSE)
#option_strikes['searchResults'][1]['tradingSymbol']
try:
    option_chain_data=samco.get_option_chain(search_symbol_name=symbol,exchange=samco.EXCHANGE_NFO,expiry_date=expiry_date_option)
except Exception as e:
        logging.info("Order placement failed: {}".format(e))
        time.sleep(185)
        option_chain_data=samco.get_option_chain(search_symbol_name=symbol,exchange=samco.EXCHANGE_NFO,expiry_date=expiry_date_option)
option_chain_df =pd.json_normalize(json.loads(option_chain_data),['optionChainDetails'])
# print(option_chain_df)
if (math.trunc(float(option_chain_df['spotPrice'][1]))%strike_scale) >30:
    adjust_scale =50
elif (math.trunc(float(option_chain_df['spotPrice'][1]))%strike_scale) <=30:
    adjust_scale =0

# CALCULATING ATM STRIKE WITH SPOT FUNCTION
def spot_price(scripname):
    last_price= int(kite.ltp(scripname)[scripname]["last_price"])
    return last_price

# CALCULATING PARAMETERS FOR ALGO 
# atm_strike=(spot_price(scrip)-(spot_price(scrip)%strike_scale)+adjust_scale)
cur_spot=spot_price(scrip)
if (math.trunc(cur_spot)%strike_scale) >30:
    adjust_scale =50
elif (math.trunc(cur_spot)%strike_scale) <=30:
    adjust_scale =0



option_chain_df['strikePrice'] = pd.to_numeric(option_chain_df['strikePrice'])
option_chain_df['lastTradedPrice'] = pd.to_numeric(option_chain_df['lastTradedPrice'])
instruments=pd.DataFrame(kite.instruments(exchange='NFO'))
# print(instruments, atm_strike)
try:
    breakeven_values=pd.read_csv(os.getcwd()+'\\current_be_range.csv')
    breakeven_range_ce = breakeven_values['breakeven_range_ce'][0]
    breakeven_range_pe = breakeven_values['breakeven_range_pe'][0]
    ce_entry_price = breakeven_values['ce_entry_price'][0]
    pe_entry_price = breakeven_values['pe_entry_price'][0]
except Exception as e:
    print('No data in breakeven file')
# GET TRADE SYMBOL FOR OPTOINS
def get_trade_symbol(strike_price,option_type):
    return instruments[(instruments['strike']==strike_price) & (instruments['expiry']==datetime.strptime(expiry_date,'%Y/%m/%d').date())&(instruments['instrument_type']==option_type)]['tradingsymbol'].iloc[0]

all_positions=pd.DataFrame(kite.positions()['net'])
open_positions=all_positions[all_positions['quantity']!=0]
open_positions['Name']=open_positions['tradingsymbol'].str.slice(0,5)
nifty_open_cnt =open_positions[open_positions['Name'] == name_idx].count()['tradingsymbol']
if nifty_open_cnt ==0:
    otm_ce_strike=(cur_spot-(cur_spot%strike_scale)+adjust_scale)+250
    otm_pe_strike=(cur_spot-(cur_spot%strike_scale)+adjust_scale)-250
    print('OTM CE STRIKE',otm_ce_strike,'OTM PE STRIKE',otm_pe_strike)
    enter_position(get_trade_symbol(otm_ce_strike,'CE'))
    ce_entry_price=spot_price('NFO:'+get_trade_symbol(otm_ce_strike,'CE'))
    enter_position(get_trade_symbol(otm_pe_strike,'PE'))
    pe_entry_price=spot_price('NFO:'+get_trade_symbol(otm_pe_strike,'PE'))
    breakeven_ce =otm_ce_strike+ce_entry_price+pe_entry_price
    breakeven_pe =otm_pe_strike-(ce_entry_price+pe_entry_price)
    print(breakeven_ce,breakeven_pe)
    breakeven_range=int (abs((breakeven_ce-breakeven_pe)/6))
    breakeven_range_ce =cur_spot +breakeven_range
    breakeven_range_pe =cur_spot -breakeven_range
    print('range',breakeven_range_ce,breakeven_range_pe)
    current_be_range=pd.DataFrame(dict({'breakeven_range_ce':[breakeven_range_ce],'breakeven_range_pe':[breakeven_range_pe],'ce_entry_price':[ce_entry_price],'pe_entry_price':[pe_entry_price],'otm_ce_strike':[otm_ce_strike],,'otm_pe_strike':[otm_pe_strike]}))
    current_be_range.to_csv(os.getcwd()+'\\current_be_range.csv')
currentDateAndTime=datetime.now()
try:
    breakeven_values=pd.read_csv(os.getcwd()+'\\current_be_range.csv')
    breakeven_range_ce = breakeven_values['breakeven_range_ce'][0]
    breakeven_range_pe = breakeven_values['breakeven_range_pe'][0]
    ce_entry_price = breakeven_values['ce_entry_price'][0]
    pe_entry_price = breakeven_values['pe_entry_price'][0]
    otm_ce_strike =breakeven_values['otm_ce_strike'][0]
    otm_pe_strike =breakeven_values['otm_pe_strike'][0]
except Exception as e:
    print('No data in breakeven file')
#try:
#    status=kite.positions()['status']
#except Exception as e:
#    status ='NOPOS'

print(nifty_open_cnt)
time.sleep(120)#sleeping just to get the order executed
all_positions=pd.DataFrame(kite.positions()['net'])
open_positions=all_positions[all_positions['quantity']!=0]
open_positions['Name']=open_positions['tradingsymbol'].str.slice(0,5)
nifty_open_cnt =open_positions[open_positions['Name'] == 'NIFTY'].count()['tradingsymbol']
print(nifty_open_cnt)
#Cancel order if both orders are not executed even after a minute
if nifty_open_cnt <2
    close_order_id=close_position(open_positions['tradingsymbol'].iloc[0])
    print('Closing order as both the orders anot executed. please check and re run')
    time.sleep(60)
while (nifty_open_cnt >1 and currentDateAndTime.hour*100+currentDateAndTime.minute >930 and currentDateAndTime.hour*100+currentDateAndTime.minute <2330):
    print('Checking ')
    print('OTM CE STRIKE',otm_ce_strike,'OTM PE STRIKE',otm_pe_strike)
    print('breakeven cepe-',breakeven_ce,breakeven_pe,'breakevene range cepe',breakeven_range_ce,breakeven_range_pe)
    currentDateAndTime=datetime.now()
    #######################################
    #option_strikes =json.loads(samco.search_equity_derivative(search_symbol_name=symbol,exchange=samco.EXCHANGE_NFO))
    ##current_price =samco.get_quote(symbol_name='NIFTY',exchange=samco.EXCHANGE_NSE)
    try:
        option_chain_data=samco.get_option_chain(search_symbol_name=symbol,exchange=samco.EXCHANGE_NFO,expiry_date=expiry_date_option)
    except Exception as e:
        print("samco failed: retrying after 3 minutes")
        time.sleep(185)
        option_chain_data=samco.get_option_chain(search_symbol_name=symbol,exchange=samco.EXCHANGE_NFO,expiry_date=expiry_date_option)
    option_chain_df =pd.json_normalize(json.loads(option_chain_data),['optionChainDetails'])
    if math.trunc(float(option_chain_df['spotPrice'][1]))%strike_scale >30:
        adjust_scale =50
    elif (math.trunc(float(option_chain_df['spotPrice'][1]))%strike_scale) <=30:
        adjust_scale =0
    # atm_strike=math.trunc(float(option_chain_df['spotPrice'][1]))-math.trunc(float(option_chain_df['spotPrice'][1]))%strike_scale+adjust_scale
    option_chain_df['strikePrice'] = pd.to_numeric(option_chain_df['strikePrice'])
    option_chain_df['lastTradedPrice'] = pd.to_numeric(option_chain_df['lastTradedPrice'])
    # ce_trade_record =option_chain_df[(option_chain_df['strikePrice']==atm_strike) & (option_chain_df['optionType']=='CE')].iloc[0]
    # pe_trade_record=option_chain_df[(option_chain_df['lastTradedPrice'] <= ce_trade_record['lastTradedPrice'])& (option_chain_df['optionType']=='PE')].sort_values(by='lastTradedPrice',ascending=False).iloc[0]
    # atm_pe_strike=pe_trade_record['strikePrice']
    # atm_strike=(spot_price(scrip)-(spot_price(scrip)%strike_scale)+adjust_scale)
    cur_spot=spot_price(scrip)
    # atm_strike=(cur_spot-(cur_spot%strike_scale)+adjust_scale)
    ##########################################
    nifty_open_cnt =open_positions[open_positions['Name'] == name_idx].count()['tradingsymbol']
    if nifty_open_cnt==2:
        all_positions=pd.DataFrame(kite.positions()['net'])
        open_positions=all_positions[all_positions['quantity']!=0]
        open_positions['Name']=open_positions['tradingsymbol'].str.slice(0,5)
        open_positions = open_positions[open_positions['Name'] == name_idx]
    #cur_positions = pd.json_normalize(json.loads(samco.get_positions_data(position_type=samco.POSITION_TYPE_DAY)))
    #print(cur_positions['status'].iloc[0])
    #if cur_positions['status'].iloc[0] !='Failure':
       # cur_position_details =pd.json_normalize(json.loads(cur_positions['positionDetails']))
        open_trade_symbol_ce=open_positions[open_positions['tradingsymbol'].str.slice(-2,)=='CE']['tradingsymbol'].iloc[0]
        open_trade_symbol_pe=open_positions[open_positions['tradingsymbol'].str.slice(-2,)=='PE']['tradingsymbol'].iloc[0]
        last_price_ce =spot_price('NFO:'+open_trade_symbol_ce)
        last_price_pe =spot_price('NFO:'+open_trade_symbol_pe)
        print(last_price_ce)
        print(last_price_pe)
        if (last_price_ce >98 or last_price_pe >last_price_ce*2):
            close_order_id=close_position(open_trade_symbol_ce)
            close_option_type='CE'
            new_strike_price =option_chain_df[(option_chain_df['lastTradedPrice']<=last_price_pe*1.1) & (option_chain_df['optionType']==close_option_type)].sort_values(by='lastTradedPrice',ascending=False).iloc[0]['strikePrice']
            enter_position(get_trade_symbol(new_strike_price,close_option_type))
            ce_entry_price=spot_price('NFO:'+get_trade_symbol(new_strike_price,close_option_type))
            otm_ce_strike=new_strike_price
            breakeven_ce =otm_ce_strike+ce_entry_price+pe_entry_price
            breakeven_pe =otm_pe_strike-(ce_entry_price+pe_entry_price)
            breakeven_range=int (abs((breakeven_ce-breakeven_pe)/6))
            breakeven_range_ce =cur_spot +breakeven_range
            breakeven_range_pe =cur_spot -breakeven_range
            current_be_range=pd.DataFrame(dict({'breakeven_range_ce':[breakeven_range_ce],'breakeven_range_pe':[breakeven_range_pe],'ce_entry_price':[ce_entry_price],'pe_entry_price':[pe_entry_price]}))
            current_be_range.to_csv(os.getcwd()+'\\current_be_range.csv')
        elif (last_price_pe >98 or last_price_ce>last_price_pe*2):
            close_order_id=close_position(open_trade_symbol_pe)
            close_option_type='PE'
            new_strike_price =option_chain_df[(option_chain_df['lastTradedPrice']<=last_price_ce*1.1) & (option_chain_df['optionType']==close_option_type)].sort_values(by='lastTradedPrice',ascending=False).iloc[0]['strikePrice']
            enter_position(get_trade_symbol(new_strike_price,close_option_type))
            pe_entry_price=spot_price('NFO:'+get_trade_symbol(new_strike_price,close_option_type))
            otm_pe_strike=new_strike_price
            breakeven_ce =otm_ce_strike+ce_entry_price+pe_entry_price
            breakeven_pe =otm_pe_strike-(ce_entry_price+pe_entry_price)
            breakeven_range=int (abs((breakeven_ce-breakeven_pe)/6))
            breakeven_range_ce =cur_spot +breakeven_range
            breakeven_range_pe =cur_spot -breakeven_range
            current_be_range=pd.DataFrame(dict({'breakeven_range_ce':[breakeven_range_ce],'breakeven_range_pe':[breakeven_range_pe],'ce_entry_price':[ce_entry_price],'pe_entry_price':[pe_entry_price]}))
            current_be_range.to_csv(os.getcwd()+'\\current_be_range.csv')
        elif spot_price(scrip)< breakeven_range_pe:
            close_order_id=close_position(open_trade_symbol_ce)
            close_option_type='CE'
            new_strike_price =option_chain_df[(option_chain_df['lastTradedPrice']<=last_price_ce*1.1) & (option_chain_df['optionType']==close_option_type)].sort_values(by='lastTradedPrice',ascending=False).iloc[0]['strikePrice']
            enter_position(get_trade_symbol(new_strike_price,close_option_type))
            ce_entry_price=spot_price('NFO:'+get_trade_symbol(new_strike_price,close_option_type))
            otm_pe_strike=new_strike_price
            breakeven_ce =otm_ce_strike+ce_entry_price+pe_entry_price
            breakeven_pe =otm_pe_strike-(ce_entry_price+pe_entry_price)
            breakeven_range=int (abs((breakeven_ce-breakeven_pe)/6))
            breakeven_range_ce =cur_spot +breakeven_range
            breakeven_range_pe =cur_spot -breakeven_range
            current_be_range=pd.DataFrame(dict({'breakeven_range_ce':[breakeven_range_ce],'breakeven_range_pe':[breakeven_range_pe],'ce_entry_price':[ce_entry_price],'pe_entry_price':[pe_entry_price]}))
            current_be_range.to_csv(os.getcwd()+'\\current_be_range.csv')            
        elif spot_price(scrip)>breakeven_range_ce:
            close_order_id=close_position(open_trade_symbol_pe)
            close_option_type='PE'
            new_strike_price =option_chain_df[(option_chain_df['lastTradedPrice']<=last_price_pe*1.1) & (option_chain_df['optionType']==close_option_type)].sort_values(by='lastTradedPrice',ascending=False).iloc[0]['strikePrice']
            enter_position(get_trade_symbol(new_strike_price,close_option_type))
            pe_entry_price=spot_price('NFO:'+get_trade_symbol(new_strike_price,close_option_type))
            otm_ce_strike=new_strike_price
            breakeven_ce =otm_ce_strike+ce_entry_price+pe_entry_price
            breakeven_pe =otm_pe_strike-(ce_entry_price+pe_entry_price)
            breakeven_range=int (abs((breakeven_ce-breakeven_pe)/6))
            breakeven_range_ce =cur_spot +breakeven_range
            breakeven_range_pe =cur_spot -breakeven_range
            current_be_range=pd.DataFrame(dict({'breakeven_range_ce':[breakeven_range_ce],'breakeven_range_pe':[breakeven_range_pe],'ce_entry_price':[ce_entry_price],'pe_entry_price':[pe_entry_price]}))
            current_be_range.to_csv(os.getcwd()+'\\current_be_range.csv')

    if (currentDateAndTime.hour*100+currentDateAndTime.minute >1440) &(currentDateAndTime.weekday()==3) :
        close_order_id=close_position(open_positions['tradingsymbol'].iloc[1])
        close_order_id=close_position(open_positions['tradingsymbol'].iloc[0])
        break
    time.sleep(refresh_time)
import os

# KITE CREDENTIALS


ZERODHA_API_KEY = open("D:\\GIST ALGOS\\INTRADAY EXPIRY ALGO\\order_access\\api_key.txt",'r').read()
ZERODHA_API_SECRET = open("D:\\GIST ALGOS\\INTRADAY EXPIRY ALGO\\order_access\\api_secret.txt",'r').read()
kite = KiteConnect(api_key=ZERODHA_API_KEY)

access_token ='oq0OUMgYUpyqfLDVVg5FJQH2xkdWLqUk'
kite.set_access_token(access_token)

#kite = KiteConnect(api_key="crriyu5vlpm08iua")
# print(kite.login_url())
# data = kite.generate_session('UR2HIYCOqqY5PdsljoCcUe8qAyOeGfp8', api_secret="r91a37hxsacj8fxxfgoyn5per201pkvk")
# print(data['access_token'])


# ALGO PARAMETERS
name_idx='NIFTY'
scrip='NSE:NIFTY 50'
symbol="NIFTY10NOV"
expiry_date='2022/11/10'#yyyy/mm/dd
expiry_date_option ='2022-11-10'#yyyy-mm-dd
strike_scale=50# for nifty.. change it to 25 for bank nifty
refresh_time =60#seconds
india_vix=kite.ltp("NSE:INDIA VIX")['NSE:INDIA VIX']['last_price']
# SAMCO CREDENTIALS FOR OPTION CHAIN -- NEED TO SHIFT WITH RESPECTIVE PLATFORM
def run_credentials():
    from snapi_py_client.snapi_bridge import StocknoteAPIPythonBridge
    samco = StocknoteAPIPythonBridge()
    login = samco.login(
        body={"userId": 'PK1197', 'password': 'alpha@12345', 'yob': '1983'})
    token = json.loads(login)['sessionToken']
    headers = {
        'Accept': 'application/json',
        'x-session-token': token,
        'login':login,
        'samco':samco
    }
    return(headers)

# ZERODHA ENTERING TRADES
def enter_position(symbolname):
    print(symbolname)
    order_id=0
    try:
        order_id = kite.place_order(tradingsymbol=symbolname,
                                exchange=kite.EXCHANGE_NFO,
                                transaction_type=kite.TRANSACTION_TYPE_SELL,
                                quantity=50,
                                variety=kite.VARIETY_REGULAR,
                                order_type=kite.ORDER_TYPE_MARKET,
                                product=kite.PRODUCT_NRML,
                                validity=kite.VALIDITY_DAY)
        logging.info("Order placed. ID is: {}".format(order_id))
        print('order id is',order_id)
    except Exception as e:
        print(e)
        logging.info("Order placement failed: {}".format(e))
        order_id=0
        print('order id is',order_id)
    return order_id

# ZERODHA CLOSING TRADES AS PER ADJUSTMENTS
def close_position(symbolname):
    order_id=0
    try:
        order_id = kite.place_order(tradingsymbol=symbolname,
                                exchange=kite.EXCHANGE_NFO,
                                transaction_type=kite.TRANSACTION_TYPE_BUY,
                                quantity=50,
                                variety=kite.VARIETY_REGULAR,
                                order_type=kite.ORDER_TYPE_MARKET,
                                product=kite.PRODUCT_NRML,
                                validity=kite.VALIDITY_DAY)

        logging.info("Order placed. ID is: {}".format(order_id))
        print('order id is',order_id)
    except Exception as e:
        logging.info("Order placement failed: {}".format(e))
        order_id=0
        print('order id is',order_id)
    return order_id

# INITIATING SAMCO PROCESS TO GET OPTION CHAIN
creds=run_credentials()
creds['samco'].set_session_token(sessionToken=creds['x-session-token'])
samco=creds['samco']
#option_strikes =json.loads(samco.search_equity_derivative(search_symbol_name=symbol,exchange=samco.EXCHANGE_NFO))
#current_price =samco.get_quote(symbol_name='NIFTY',exchange=samco.EXCHANGE_NSE)
#option_strikes['searchResults'][1]['tradingSymbol']
try:
    option_chain_data=samco.get_option_chain(search_symbol_name=symbol,exchange=samco.EXCHANGE_NFO,expiry_date=expiry_date_option)
except Exception as e:
        logging.info("Order placement failed: {}".format(e))
        time.sleep(185)
        option_chain_data=samco.get_option_chain(search_symbol_name=symbol,exchange=samco.EXCHANGE_NFO,expiry_date=expiry_date_option)
option_chain_df =pd.json_normalize(json.loads(option_chain_data),['optionChainDetails'])
# print(option_chain_df)
if (math.trunc(float(option_chain_df['spotPrice'][1]))%strike_scale) >30:
    adjust_scale =50
elif (math.trunc(float(option_chain_df['spotPrice'][1]))%strike_scale) <=30:
    adjust_scale =0

# CALCULATING ATM STRIKE WITH SPOT FUNCTION
def spot_price(scripname):
    last_price= int(kite.ltp(scripname)[scripname]["last_price"])
    return last_price

# CALCULATING PARAMETERS FOR ALGO 
# atm_strike=(spot_price(scrip)-(spot_price(scrip)%strike_scale)+adjust_scale)
cur_spot=spot_price(scrip)
if (math.trunc(cur_spot)%strike_scale) >30:
    adjust_scale =50
elif (math.trunc(cur_spot)%strike_scale) <=30:
    adjust_scale =0

otm_ce_strike=(cur_spot-(cur_spot%strike_scale)+adjust_scale)+250
otm_pe_strike=(cur_spot-(cur_spot%strike_scale)+adjust_scale)-250

print('OTM CE STRIKE',otm_ce_strike)
print('OTM PE STRIKE',otm_pe_strike)

option_chain_df['strikePrice'] = pd.to_numeric(option_chain_df['strikePrice'])
option_chain_df['lastTradedPrice'] = pd.to_numeric(option_chain_df['lastTradedPrice'])
instruments=pd.DataFrame(kite.instruments(exchange='NFO'))
# print(instruments, atm_strike)
try:
    breakeven_values=pd.read_csv(os.getcwd()+'\\current_be_range.csv')
    breakeven_range_ce = breakeven_values['breakeven_range_ce'][0]
    breakeven_range_pe = breakeven_values['breakeven_range_pe'][0]
    ce_entry_price = breakeven_values['ce_entry_price'][0]
    pe_entry_price = breakeven_values['pe_entry_price'][0]
except Exception as e:
    print('No data in breakeven file')
# GET TRADE SYMBOL FOR OPTOINS
def get_trade_symbol(strike_price,option_type):
    return instruments[(instruments['strike']==strike_price) & (instruments['expiry']==datetime.strptime(expiry_date,'%Y/%m/%d').date())&(instruments['instrument_type']==option_type)]['tradingsymbol'].iloc[0]

all_positions=pd.DataFrame(kite.positions()['net'])
open_positions=all_positions[all_positions['quantity']!=0]
open_positions['Name']=open_positions['tradingsymbol'].str.slice(0,5)
nifty_open_cnt =open_positions[open_positions['Name'] == name_idx].count()['tradingsymbol']
if nifty_open_cnt ==0:
    enter_position(get_trade_symbol(otm_ce_strike,'CE'))
    ce_entry_price=spot_price('NFO:'+get_trade_symbol(otm_ce_strike,'CE'))
    enter_position(get_trade_symbol(otm_pe_strike,'PE'))
    pe_entry_price=spot_price('NFO:'+get_trade_symbol(otm_pe_strike,'PE'))
    breakeven_ce =otm_ce_strike+ce_entry_price+pe_entry_price
    breakeven_pe =otm_pe_strike-(ce_entry_price+pe_entry_price)
    breakeven_range=int (abs((breakeven_ce-breakeven_pe)/6))
    breakeven_range_ce =cur_spot +breakeven_range
    breakeven_range_pe =cur_spot -breakeven_range
    current_be_range=pd.DataFrame(dict({'breakeven_range_ce':[breakeven_range_ce],'breakeven_range_pe':[breakeven_range_pe],'ce_entry_price':[ce_entry_price],'pe_entry_price':[pe_entry_price]}))
    current_be_range.to_csv(os.getcwd()+'\\current_be_range.csv')
currentDateAndTime=datetime.now()
#try:
#    status=kite.positions()['status']
#except Exception as e:
#    status ='NOPOS'

print(nifty_open_cnt)
time.sleep(120)#sleeping just to get the order executed
all_positions=pd.DataFrame(kite.positions()['net'])
open_positions=all_positions[all_positions['quantity']!=0]
open_positions['Name']=open_positions['tradingsymbol'].str.slice(0,5)
nifty_open_cnt =open_positions[open_positions['Name'] == 'NIFTY'].count()['tradingsymbol']
print(nifty_open_cnt)
#Cancel order if both orders are not executed even after a minute
if nifty_open_cnt <2
    close_order_id=close_position(open_positions['tradingsymbol'].iloc[0])
    print('Closing order as both the orders anot executed. please check and re run')
    time.sleep(60)
while (nifty_open_cnt >1 and currentDateAndTime.hour*100+currentDateAndTime.minute >930 and currentDateAndTime.hour*100+currentDateAndTime.minute <2330):
    print('inside')
    currentDateAndTime=datetime.now()
    #######################################
    #option_strikes =json.loads(samco.search_equity_derivative(search_symbol_name=symbol,exchange=samco.EXCHANGE_NFO))
    ##current_price =samco.get_quote(symbol_name='NIFTY',exchange=samco.EXCHANGE_NSE)
    try:
        option_chain_data=samco.get_option_chain(search_symbol_name=symbol,exchange=samco.EXCHANGE_NFO,expiry_date=expiry_date_option)
    except Exception as e:
        print("samco failed: retrying after 3 minutes")
        time.sleep(185)
        option_chain_data=samco.get_option_chain(search_symbol_name=symbol,exchange=samco.EXCHANGE_NFO,expiry_date=expiry_date_option)
    option_chain_df =pd.json_normalize(json.loads(option_chain_data),['optionChainDetails'])
    if math.trunc(float(option_chain_df['spotPrice'][1]))%strike_scale >30:
        adjust_scale =50
    elif (math.trunc(float(option_chain_df['spotPrice'][1]))%strike_scale) <=30:
        adjust_scale =0
    # atm_strike=math.trunc(float(option_chain_df['spotPrice'][1]))-math.trunc(float(option_chain_df['spotPrice'][1]))%strike_scale+adjust_scale
    option_chain_df['strikePrice'] = pd.to_numeric(option_chain_df['strikePrice'])
    option_chain_df['lastTradedPrice'] = pd.to_numeric(option_chain_df['lastTradedPrice'])
    # ce_trade_record =option_chain_df[(option_chain_df['strikePrice']==atm_strike) & (option_chain_df['optionType']=='CE')].iloc[0]
    # pe_trade_record=option_chain_df[(option_chain_df['lastTradedPrice'] <= ce_trade_record['lastTradedPrice'])& (option_chain_df['optionType']=='PE')].sort_values(by='lastTradedPrice',ascending=False).iloc[0]
    # atm_pe_strike=pe_trade_record['strikePrice']
    # atm_strike=(spot_price(scrip)-(spot_price(scrip)%strike_scale)+adjust_scale)
    cur_spot=spot_price(scrip)
    # atm_strike=(cur_spot-(cur_spot%strike_scale)+adjust_scale)
    ##########################################
    nifty_open_cnt =open_positions[open_positions['Name'] == name_idx].count()['tradingsymbol']
    if nifty_open_cnt==2:
        all_positions=pd.DataFrame(kite.positions()['net'])
        open_positions=all_positions[all_positions['quantity']!=0]
        open_positions['Name']=open_positions['tradingsymbol'].str.slice(0,5)
        open_positions = open_positions[open_positions['Name'] == name_idx]
    #cur_positions = pd.json_normalize(json.loads(samco.get_positions_data(position_type=samco.POSITION_TYPE_DAY)))
    #print(cur_positions['status'].iloc[0])
    #if cur_positions['status'].iloc[0] !='Failure':
       # cur_position_details =pd.json_normalize(json.loads(cur_positions['positionDetails']))
        open_trade_symbol_ce=open_positions[open_positions['tradingsymbol'].str.slice(-2,)=='CE']['tradingsymbol'].iloc[0]
        open_trade_symbol_pe=open_positions[open_positions['tradingsymbol'].str.slice(-2,)=='PE']['tradingsymbol'].iloc[0]
        last_price_ce =spot_price('NFO:'+open_trade_symbol_ce)
        last_price_pe =spot_price('NFO:'+open_trade_symbol_pe)
        print(last_price_ce)
        print(last_price_pe)
        if (last_price_ce >98 or last_price_pe >last_price_ce*2):
            close_order_id=close_position(open_trade_symbol_ce)
            close_option_type='CE'
            new_strike_price =option_chain_df[(option_chain_df['lastTradedPrice']<=last_price_pe*1.1) & (option_chain_df['optionType']==close_option_type)].sort_values(by='lastTradedPrice',ascending=False).iloc[0]['strikePrice']
            enter_position(get_trade_symbol(new_strike_price,close_option_type))
            ce_entry_price=spot_price('NFO:'+get_trade_symbol(new_strike_price,close_option_type))
            otm_ce_strike=new_strike_price
            breakeven_ce =otm_ce_strike+ce_entry_price+pe_entry_price
            breakeven_pe =otm_pe_strike-(ce_entry_price+pe_entry_price)
            breakeven_range=int (abs((breakeven_ce-breakeven_pe)/6))
            breakeven_range_ce =cur_spot +breakeven_range
            breakeven_range_pe =cur_spot -breakeven_range
            current_be_range=pd.DataFrame(dict({'breakeven_range_ce':[breakeven_range_ce],'breakeven_range_pe':[breakeven_range_pe],'ce_entry_price':[ce_entry_price],'pe_entry_price':[pe_entry_price]}))
            current_be_range.to_csv(os.getcwd()+'\\current_be_range.csv')
        elif (last_price_pe >98 or last_price_ce>last_price_pe*2):
            close_order_id=close_position(open_trade_symbol_pe)
            close_option_type='PE'
            new_strike_price =option_chain_df[(option_chain_df['lastTradedPrice']<=last_price_ce*1.1) & (option_chain_df['optionType']==close_option_type)].sort_values(by='lastTradedPrice',ascending=False).iloc[0]['strikePrice']
            enter_position(get_trade_symbol(new_strike_price,close_option_type))
            pe_entry_price=spot_price('NFO:'+get_trade_symbol(new_strike_price,close_option_type))
            otm_pe_strike=new_strike_price
            breakeven_ce =otm_ce_strike+ce_entry_price+pe_entry_price
            breakeven_pe =otm_pe_strike-(ce_entry_price+pe_entry_price)
            breakeven_range=int (abs((breakeven_ce-breakeven_pe)/6))
            breakeven_range_ce =cur_spot +breakeven_range
            breakeven_range_pe =cur_spot -breakeven_range
            current_be_range=pd.DataFrame(dict({'breakeven_range_ce':[breakeven_range_ce],'breakeven_range_pe':[breakeven_range_pe],'ce_entry_price':[ce_entry_price],'pe_entry_price':[pe_entry_price]}))
            current_be_range.to_csv(os.getcwd()+'\\current_be_range.csv')
        elif spot_price(scrip)< breakeven_range_pe:
            close_order_id=close_position(open_trade_symbol_ce)
            close_option_type='CE'
            new_strike_price =option_chain_df[(option_chain_df['lastTradedPrice']<=last_price_ce*1.1) & (option_chain_df['optionType']==close_option_type)].sort_values(by='lastTradedPrice',ascending=False).iloc[0]['strikePrice']
            enter_position(get_trade_symbol(new_strike_price,close_option_type))
            ce_entry_price=spot_price('NFO:'+get_trade_symbol(new_strike_price,close_option_type))
            otm_pe_strike=new_strike_price
            breakeven_ce =otm_ce_strike+ce_entry_price+pe_entry_price
            breakeven_pe =otm_pe_strike-(ce_entry_price+pe_entry_price)
            breakeven_range=int (abs((breakeven_ce-breakeven_pe)/6))
            breakeven_range_ce =cur_spot +breakeven_range
            breakeven_range_pe =cur_spot -breakeven_range
            current_be_range=pd.DataFrame(dict({'breakeven_range_ce':[breakeven_range_ce],'breakeven_range_pe':[breakeven_range_pe],'ce_entry_price':[ce_entry_price],'pe_entry_price':[pe_entry_price]}))
            current_be_range.to_csv(os.getcwd()+'\\current_be_range.csv')            
        elif spot_price(scrip)>breakeven_range_ce:
            close_order_id=close_position(open_trade_symbol_pe)
            close_option_type='PE'
            new_strike_price =option_chain_df[(option_chain_df['lastTradedPrice']<=last_price_pe*1.1) & (option_chain_df['optionType']==close_option_type)].sort_values(by='lastTradedPrice',ascending=False).iloc[0]['strikePrice']
            enter_position(get_trade_symbol(new_strike_price,close_option_type))
            pe_entry_price=spot_price('NFO:'+get_trade_symbol(new_strike_price,close_option_type))
            otm_ce_strike=new_strike_price
            breakeven_ce =otm_ce_strike+ce_entry_price+pe_entry_price
            breakeven_pe =otm_pe_strike-(ce_entry_price+pe_entry_price)
            breakeven_range=int (abs((breakeven_ce-breakeven_pe)/6))
            breakeven_range_ce =cur_spot +breakeven_range
            breakeven_range_pe =cur_spot -breakeven_range
            current_be_range=pd.DataFrame(dict({'breakeven_range_ce':[breakeven_range_ce],'breakeven_range_pe':[breakeven_range_pe],'ce_entry_price':[ce_entry_price],'pe_entry_price':[pe_entry_price]}))
            current_be_range.to_csv(os.getcwd()+'\\current_be_range.csv')

    if (currentDateAndTime.hour*100+currentDateAndTime.minute >1440) &(currentDateAndTime.weekday()==3) :
        close_order_id=close_position(open_positions['tradingsymbol'].iloc[1])
        close_order_id=close_position(open_positions['tradingsymbol'].iloc[0])
        break
    time.sleep(refresh_time)
