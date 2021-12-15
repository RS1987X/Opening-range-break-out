# -*- coding: utf-8 -*-
"""
Created on Sun Dec 12 13:57:44 2021

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

evo_data = pd.read_csv('OMXSTO_DLY_VOLCAR_B, 15.csv')
evo_data = evo_data['time;open;high;low;close;VWAP;Upper Band;Lower Band;Volume;Volume MA'].str.split(";",expand=True)
evo_data = evo_data.rename(columns={0:"DateTime", 1:"Open", 2:"High", 3:"Low", 4:"Close", 5:"VWAP", 6:"Upper Band", 7:"Lower Band", 8:"Volume", 9:"Volume MA"})
evo_data = evo_data[["DateTime","Open","High", "Low", "Close","Volume"]]



time_offset_removed =  evo_data["DateTime"].str[:-6]
only_date_part = evo_data["DateTime"].str[:-15]
only_time_part = time_offset_removed.str[11:]

evo_data.insert(1,"DatePart", only_date_part) 
evo_data.insert(2,"TimePart", only_time_part) 




#Closing prices for the trading session, full and half session
full_day_dates = evo_data[evo_data["TimePart"] == "17:15:00"]["DatePart"].to_frame()
all_dates =  evo_data[evo_data["TimePart"] == "09:00:00"]["DatePart"].to_frame()
idx = np.where(all_dates.merge(full_day_dates,how="left",indicator=True)["_merge"] == "left_only")
half_day_dates = all_dates.iloc[idx]["DatePart"].to_frame()
half_days_data = evo_data[evo_data["DatePart"].isin(half_day_dates["DatePart"])]
half_days_data["TimePart"] == "12:45:00"


#DAY HIGH and DAY LOWS
dh = evo_data.groupby('DatePart')["High"].max().to_frame()
dl = evo_data.groupby('DatePart')["Low"].min().to_frame()

#EXIT PRICES for both half and full sessions
exit_price_half_day = half_days_data[half_days_data["TimePart"] == "12:45:00"]["Close"]
exit_price_full_days = evo_data[evo_data["TimePart"] == "17:15:00"]["Close"]
exit_price = exit_price_full_days.append(exit_price_half_day)

exit_price = exit_price.sort_index()
exit_price = exit_price.to_frame().astype(float)
exit_price.insert(1,"DatePart",only_date_part)
exit_price = exit_price.set_index("DatePart")

#OPENING RANGE
opening_rng_high = evo_data[evo_data["TimePart"] == "09:00:00"]["High"].to_frame()
#opening_rng_high = opening_rng_high.to_frame()
opening_rng_high.insert(1,"DatePart",only_date_part)
opening_rng_high = opening_rng_high.set_index("DatePart")


opening_rng_low = evo_data[evo_data["TimePart"] == "09:00:00"]["Low"].to_frame()
#opening_rng_high = opening_rng_high.to_frame()
opening_rng_low.insert(1,"DatePart",only_date_part)
opening_rng_low = opening_rng_low.set_index("DatePart")

#OPEN BAR VOLUME
opening_rng_volume = evo_data[evo_data["TimePart"] == "09:00:00"]["Volume"].to_frame()
opening_rng_volume.insert(1,"DatePart",only_date_part)
opening_rng_volume = opening_rng_volume.set_index("DatePart")

#OPENING GAP 
open_price = evo_data[evo_data["TimePart"] == "09:00:00"]["Open"].to_frame().astype(float)
open_price.insert(1,"DatePart",only_date_part)
open_price = open_price.set_index("DatePart")
opening_gap = open_price["Open"]/exit_price["Close"].shift(1)-1


#long position logic
dh_above_opening_high = (dh > opening_rng_high)
low_opening_rng_volume = (opening_rng_volume["Volume"].astype(int) < (7*150000)).to_frame()

#short position logic
#dl_below_opening_low = (dh > opening_rng_high)
#low_opening_rng_volume = (opening_rng_volume["Volume"].astype(int) > 300000).to_frame()


pos_ind = (dh_above_opening_high["High"])  & (low_opening_rng_volume["Volume"]) & (opening_gap >= 0.0)
entry_price = opening_rng_high[pos_ind].astype(float)


#entry_price_no_nan = entry_price[~entry_price["High"].isnull()].astype(float)
#exit_price_no_nan = exit_price[~entry_price["High"].isnull()].astype(float)


#is stop loss hit?
#exit_price[exit_price["Close"].astype(float) < opening_rng_low["Low"].astype(float)] =  opening_rng_low
#TAKE OUT closing prices where we had an trade
exit_price = exit_price[pos_ind].astype(float)


#calculate reutrns
comm = 0.0002
slippage = 0.1/100
strat_returns = exit_price["Close"]/entry_price["High"]-1-comm*2-slippage



print("avg return " + str(strat_returns.mean()))
print("volatility " + str(strat_returns.std()))

kelly_f = strat_returns.mean()/(strat_returns.std()**2)
print("kelly f " + str(kelly_f))
percent_profitable = (strat_returns > 0).sum()/len(strat_returns)
print("Percent profitable " + str(percent_profitable))
############################################
##stats for basic strategy
###########################################
cum_ret =(1 + strat_returns).cumprod()
total_return = cum_ret.tail(1)-1
print("Total return " + str(total_return[0]))
print("Number of trades " + str(len(strat_returns)))
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