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
from statsmodels.graphics.tsaplots import plot_acf

evo_data = pd.read_csv('OMXSTO_DLY_SBB_B, 15.csv')
evo_data = evo_data['time;open;high;low;close;VWAP;Upper Band;Lower Band;Volume;Volume MA'].str.split(";",expand=True)
evo_data = evo_data.rename(columns={0:"DateTime", 1:"Open", 2:"High", 3:"Low", 4:"Close", 5:"VWAP", 6:"Upper Band", 7:"Lower Band", 8:"Volume", 9:"Volume MA"})
evo_data = evo_data[["DateTime","Open","High", "Low", "Close","Volume"]]


time_offset_removed =  evo_data["DateTime"].str[:-6]
only_date_part = evo_data["DateTime"].str[:-15]
only_time_part = time_offset_removed.str[11:]

evo_data.insert(1,"DatePart", only_date_part) 
evo_data.insert(2,"TimePart", only_time_part)


#DAY HIGH and DAY LOWS
dh = evo_data.groupby('DatePart')["High"].max().to_frame()
dl = evo_data.groupby('DatePart')["Low"].min().to_frame()

#Closing prices for the trading session, full and half session
full_day_dates = evo_data[evo_data["TimePart"] == "17:15:00"]["DatePart"].to_frame()
all_dates =  evo_data[evo_data["TimePart"] == "09:00:00"]["DatePart"].to_frame()
idx = np.where(all_dates.merge(full_day_dates,how="left",indicator=True)["_merge"] == "left_only")
half_day_dates = all_dates.iloc[idx]["DatePart"].to_frame()
half_days_data = evo_data[evo_data["DatePart"].isin(half_day_dates["DatePart"])]
half_days_data["TimePart"] == "12:45:00"


#EXIT PRICES for both half and full sessions
exit_price_half_day = half_days_data[half_days_data["TimePart"] == "12:45:00"]["Close"]
exit_price_full_days = evo_data[evo_data["TimePart"] == "17:15:00"]["Close"]
exit_price = exit_price_full_days.append(exit_price_half_day)

exit_price = exit_price.sort_index()
exit_price = exit_price.to_frame().astype(float)
exit_price.insert(1,"DatePart",only_date_part)
exit_price = exit_price.set_index("DatePart")



#calculate realized variance using 680 (15 min) observations, roughly 20 trading sessions
returns = evo_data["Close"].astype(float).pct_change()**2
realized_volatility = np.sqrt(returns.rolling(680).sum().astype(float)).to_frame()

#realized_volatility.insert(1,"TimePart",only_time_part)
#realized_volatility.insert(2,"DatePart", only_date_part)
#realized_volatility = realized_volatility.set_index("TimePart")
#realized_volatility_daily = realized_volatility[realized_volatility.index == "17:15:00"]

#avg_realized_vol = realized_volatility.rolling(680).mean().shift(1).to_frame()
#avg_realized_vol.insert(1,"DatePart",only_date_part)
#avg_realized_vol = avg_realized_vol.set_index("DatePart")

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

#calculate rolling 20 session opening range volume
avg_rolling_opening_volume = opening_rng_volume.rolling(20).mean().shift(1)

#OPENING GAP 
open_price = evo_data[evo_data["TimePart"] == "09:00:00"]["Open"].to_frame().astype(float)
open_price.insert(1,"DatePart",only_date_part)
open_price = open_price.set_index("DatePart")
opening_gap = open_price["Open"]/exit_price["Close"].shift(1)-1


opening_rng_pct = (opening_rng_high["High"].astype(float) - opening_rng_low["Low"].astype(float))/(opening_rng_high["High"].astype(float) + opening_rng_low["Low"].astype(float)).mean()

#long position logic
dh_above_opening_high = (dh > opening_rng_high)
low_opening_rng_volume = (opening_rng_volume["Volume"].astype(float) < 0.5*avg_rolling_opening_volume["Volume"]).to_frame()

#short position logic
dl_below_opening_low = (dl < opening_rng_low)
high_opening_rng_volume = (opening_rng_volume["Volume"].astype(float) > 1.5*avg_rolling_opening_volume["Volume"]).to_frame()


pos_ind = (dh_above_opening_high["High"])  & (opening_rng_pct < 0.02) & (opening_gap > 0.0)  & (low_opening_rng_volume["Volume"])
short_pos_ind = (high_opening_rng_volume["Volume"]) & (dl_below_opening_low["Low"]) & (opening_gap < 0.0) & (opening_rng_pct < 0.02) 

long_entry_price = opening_rng_high[pos_ind].astype(float)
short_entry_price = opening_rng_low[short_pos_ind].astype(float)

#entry_price_no_nan = entry_price[~entry_price["High"].isnull()].astype(float)
#exit_price_no_nan = exit_price[~entry_price["High"].isnull()].astype(float)

#is stop loss hit?
#exit_price[exit_price["Close"].astype(float) < opening_rng_low["Low"].astype(float)] =  opening_rng_low
#TAKE OUT closing prices where we had an trade
long_exit_price = exit_price[pos_ind].astype(float)
short_exit_price = exit_price[short_pos_ind].astype(float)

#calculate reutrns
comm = 0.0002
slippage = 0.15/100
long_strat_returns = long_exit_price["Close"]/long_entry_price["High"]-1-comm*2-slippage
short_strat_returns = short_entry_price["Low"]/short_exit_price["Close"]-1-comm*2-slippage

long_short_returns =pd.concat([long_strat_returns, short_strat_returns],axis=0) #
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


long_kelly_f = long_strat_returns.mean()/long_strat_returns.std()**2
short_kelly_f = short_strat_returns.mean()/short_strat_returns.std()**2

print("Long kelly " + str(long_kelly_f))
print("Short kelly " + str(short_kelly_f))

print("Average realized volatility " + str(realized_volatility.mean()))

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