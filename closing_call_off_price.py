# -*- coding: utf-8 -*-
"""
Created on Thu Dec 23 12:14:20 2021

@author: richa
"""


import pandas as pd
import math
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from datetime import date
from datetime import datetime
from dateutil import parser
from statsmodels.graphics.tsaplots import plot_acf

evo_data = pd.read_csv('OMXSTO_DLY_BOOZT, 15.csv')
evo_data = evo_data['time;open;high;low;close;VWAP;Upper Band;Lower Band;Volume;Volume MA'].str.split(";",expand=True)
evo_data = evo_data.rename(columns={0:"DateTime", 1:"Open", 2:"High", 3:"Low", 4:"Close", 5:"VWAP", 6:"Upper Band", 7:"Lower Band", 8:"Volume", 9:"Volume MA"})
evo_data = evo_data[["DateTime","Open","High", "Low", "Close","Volume","VWAP"]]

time_offset_removed =  evo_data["DateTime"].str[:-6]
only_date_part = evo_data["DateTime"].str[:-15]
only_time_part = time_offset_removed.str[11:]

evo_data.insert(1,"DatePart", only_date_part) 
evo_data.insert(2,"TimePart", only_time_part)

#calculate realized variance using 680 (15 min) observations, roughly 20 trading sessions
returns = evo_data["Close"].astype(float).pct_change()**2
realized_volatility = math.sqrt(252/20)*np.sqrt(returns.rolling(680).sum().astype(float)).to_frame()


#Closing prices for the trading session, full and half session
full_day_dates = evo_data[evo_data["TimePart"] == "17:15:00"]["DatePart"].to_frame()
all_dates =  evo_data[evo_data["TimePart"] == "09:00:00"]["DatePart"].to_frame()
idx = np.where(all_dates.merge(full_day_dates,how="left",indicator=True)["_merge"] == "left_only")
half_day_dates = all_dates.iloc[idx]["DatePart"].to_frame()
half_days_data = evo_data[evo_data["DatePart"].isin(half_day_dates["DatePart"])]
half_days_data["TimePart"] == "12:45:00"

#close PRICES for both half and full sessions
close_price_half_day = half_days_data[half_days_data["TimePart"] == "12:45:00"]["Close"]
close_price_full_days = evo_data[evo_data["TimePart"] == "17:15:00"]["Close"]
close_price = close_price_full_days.append(close_price_half_day)

close_price = close_price.sort_index()
close_price = close_price.to_frame().astype(float)
close_price.insert(1,"DatePart",only_date_part)
close_price = close_price.set_index("DatePart")

#pre call PRICES for both half and full sessions
precall_price_half_day = half_days_data[half_days_data["TimePart"] == "12:45:00"]["Open"]
precall_price_full_days = evo_data[evo_data["TimePart"] == "17:15:00"]["Open"]
precall_price = precall_price_full_days.append(precall_price_half_day)

precall_price = precall_price.sort_index()
precall_price = precall_price.to_frame().astype(float)
precall_price.insert(1,"DatePart",only_date_part)
precall_price = precall_price.set_index("DatePart")


#open PRICES for both half and full sessions
#open_price_half_day = half_days_data[half_days_data["TimePart"] == "09:30:00"]["Open"]
open_price = (evo_data[evo_data["TimePart"] == "09:00:00"]["Open"].astype(float) + evo_data[evo_data["TimePart"] == "09:00:00"]["Close"].astype(float))/2
#open_price = open_price_full_days.append(open_price_half_day)
open_price.columns = ["Open"]
#open_price = open_price.sort_index()
open_price = open_price.to_frame().astype(float)
open_price.insert(1,"DatePart",only_date_part)
open_price = open_price.set_index("DatePart")
open_price.columns = ["Open"]

#calc returns
comm = 0.0002
slippage = 0.1/100

#calculate volatility
ret = close_price["Close"]/close_price["Close"].shift(1)-1
vol = ret.rolling(20).std()

#beginning of day hedging leading to gap continuation first half hour, calculate returns
long_pos = (close_price["Close"]-precall_price["Open"])/precall_price["Open"] < -0.015
short_pos =(close_price["Close"]-precall_price["Open"])/precall_price["Open"] > 0.015

on_long_returns = open_price["Open"].shift(-1)/close_price["Close"]-1-comm*2-slippage
on_short_returns = close_price["Close"]/open_price["Open"].shift(-1)-1-comm*2-slippage

long_returns = on_long_returns[long_pos]
short_returns = on_short_returns[short_pos]



# #calculate rest of day (ROD) returns
# ret_rod = LH_price["Close"]/exit_price["Close"].shift(1)-1
# ret_lh = exit_price["Close"]/LH_price["Close"]-1

# long_pos_ind = ret_rod > 0.3
# short_pos_ind =  ret_rod < -0.02


# #calculate reutrns

# long_returns = ret_lh[long_pos_ind].astype(float)-comm*2-slippage
# short_returns = -1*ret_lh[short_pos_ind].astype(float)-comm*2-slippage


long_short_returns = pd.concat([long_returns, short_returns],axis=0)
long_short_returns = long_short_returns.sort_index()

print("avg return " + str(long_short_returns.mean()))
print("volatility " + str(long_short_returns.std()))

kelly_f = long_short_returns.mean()/(long_short_returns.std()**2)
print("kelly f " + str(kelly_f))
percent_profitable = (long_short_returns > 0).sum()/len(long_short_returns)
print("Percent profitable " + str(percent_profitable))

#plot_acf(short_strat_returns)

############################################
##stats for basic strategy
###########################################
cum_ret =(1 + long_short_returns).cumprod()
total_return = cum_ret.tail(1)-1
print("Total return " + str(total_return[0]))
print("Number of trades " + str(len(long_short_returns)))


long_kelly_f = long_returns.mean()/(long_returns.std()**2)
short_kelly_f = short_returns.mean()/(short_returns.std()**2)

print("Long kelly " + str(long_kelly_f))
print("Short kelly " + str(short_kelly_f))


#underlying stats
daily_returns = close_price["Close"]/close_price["Close"].shift(1)-1


print("Stock overnight return " + str(on_long_returns.mean()))
print("Stock overnight vol " + str(on_long_returns.std()))
print("Stock overnight kelly f " + str(on_long_returns.mean()/(on_long_returns.std()**2)))

#print("Average realized volatility " + str(realized_volatility.mean()))

#print("   ")
#print('Opening range break out')
#mean_ret = cum_ret.tail(1)**(1/7)-1
##print("CAGR " + str(mean_ret[0]))

#vol = (strat_returns.std()*math.sqrt(252))
#sharpe = mean_ret/vol
#kelly_f = mean_ret/vol**2
#print("Volatility " + str(vol))
#print("Sharpe " + str(sharpe[0]))
#print("Kelly fraction " + str(kelly_f[0]))
##maxiumum drawdown
#Roll_Max = cum_ret.cummax()
#Daily_Drawdown = cum_ret/Roll_Max - 1.0
#Max_Daily_Drawdown = Daily_Drawdown.cummin()
#print("Max drawdown " + str(Max_Daily_Drawdown.tail(1)[0]))
#
##plots
plt.plot(cum_ret)
##plt.plot(cum_long_ret)
##plt.plot(cum_short_ret)
#plt.plot(Daily_Drawdown)
#group by date and save high value it is day high (DH)

#if day high is same as high in first bar of day ie opening range then no trade
#if not then entry is opening range high + slippage

# exit is close of bar with time 17.15



#dates = evo_data.index.str.split(",")
#yourdate = parser.parse(dates)