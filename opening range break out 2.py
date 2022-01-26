# -*- coding: utf-8 -*-
"""
Created on Mon Jan 17 14:12:34 2022

@author: richa
"""

import pandas as pd
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy import stats
from datetime import date
from datetime import datetime
from dateutil import parser
from statsmodels.graphics.tsaplots import plot_acf

data = pd.read_csv('OMXSTO_DLY_SECU_B, 15.csv')
#evo_data = pd.read_csv('OMXSTO_DLY_INDT, 15.csv')

time_offset_removed =  data["time"].str[:-6]
only_date_part = data["time"].str[:-15]
only_time_part = time_offset_removed.str[11:]

data.insert(1,"DatePart", only_date_part) 
data.insert(2,"TimePart", only_time_part)


#DAY HIGH and DAY LOWS
dh = data.groupby('DatePart')["high"].max().to_frame()
dl = data.groupby('DatePart')["low"].min().to_frame()

#Closing prices for the trading session, full and half session
full_day_dates = data[data["TimePart"] == "17:15:00"]["DatePart"].to_frame()
all_dates =  data[data["TimePart"] == "09:00:00"]["DatePart"].to_frame()
idx = np.where(all_dates.merge(full_day_dates,how="left",indicator=True)["_merge"] == "left_only")
half_day_dates = all_dates.iloc[idx]["DatePart"].to_frame()
half_days_data = data[data["DatePart"].isin(half_day_dates["DatePart"])]
half_days_data["TimePart"] == "12:45:00"


#EXIT PRICES for both half and full sessions
exit_price_half_day = half_days_data[half_days_data["TimePart"] == "12:45:00"]["close"]
exit_price_full_days = data[data["TimePart"] == "17:15:00"]["close"]
exit_price = exit_price_full_days.append(exit_price_half_day)

exit_price = exit_price.sort_index()
exit_price = exit_price.to_frame().astype(float)
exit_price.insert(1,"DatePart",only_date_part)
exit_price = exit_price.set_index("DatePart")



#calculate realized variance using 680 (15 min) observations, roughly 20 trading sessions
returns = data["close"].astype(float).pct_change()**2
realized_volatility = np.sqrt(returns.rolling(680).sum().astype(float)).to_frame()

#realized_volatility.insert(1,"TimePart",only_time_part)
#realized_volatility.insert(2,"DatePart", only_date_part)
#realized_volatility = realized_volatility.set_index("TimePart")
#realized_volatility_daily = realized_volatility[realized_volatility.index == "17:15:00"]

#avg_realized_vol = realized_volatility.rolling(680).mean().shift(1).to_frame()
#avg_realized_vol.insert(1,"DatePart",only_date_part)
#avg_realized_vol = avg_realized_vol.set_index("DatePart")

#OPENING RANGE
opening_rng_high = data[data["TimePart"] == "09:00:00"]["high"].to_frame()
#opening_rng_high = opening_rng_high.to_frame()
opening_rng_high.insert(1,"DatePart",only_date_part)
opening_rng_high = opening_rng_high.set_index("DatePart")


opening_rng_low = data[data["TimePart"] == "09:00:00"]["low"].to_frame()
#opening_rng_high = opening_rng_high.to_frame()
opening_rng_low.insert(1,"DatePart",only_date_part)
opening_rng_low = opening_rng_low.set_index("DatePart")

#OPEN BAR VOLUME
opening_rng_volume = data[data["TimePart"] == "09:00:00"]["Volume"].to_frame()
opening_rng_volume.insert(1,"DatePart",only_date_part)
opening_rng_volume = opening_rng_volume.set_index("DatePart")

#calculate rolling 20 session opening range volume
avg_rolling_opening_volume = opening_rng_volume.rolling(20).mean().shift(1)

#OPENING GAP 
open_price = data[data["TimePart"] == "09:00:00"]["open"].to_frame().astype(float)
open_price.insert(1,"DatePart",only_date_part)
open_price = open_price.set_index("DatePart")
opening_gap = open_price["open"]/exit_price["close"].shift(1)-1

opening_rng_pct = (opening_rng_high["high"].astype(float) - opening_rng_low["low"].astype(float))/(opening_rng_high["high"].astype(float) + opening_rng_low["low"].astype(float)).mean()

#long position logic
dh_above_opening_high = (dh > opening_rng_high)
low_opening_rng_volume = (opening_rng_volume["Volume"].astype(float) < 1*avg_rolling_opening_volume["Volume"]).to_frame()

#short position logic
dl_below_opening_low = (dl < opening_rng_low)
high_opening_rng_volume = (opening_rng_volume["Volume"].astype(float) > 1.5*avg_rolling_opening_volume["Volume"]).to_frame()

short_pos_ind = (dl_below_opening_low["low"]) & (opening_gap < 0.0) & (high_opening_rng_volume["Volume"]) & (opening_rng_pct < 0.02)
pos_ind = (dh_above_opening_high["high"]) & (opening_rng_pct < 0.02) & (opening_gap > 0.0)  & (low_opening_rng_volume["Volume"])


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
slippage = 0.25/100
long_strat_returns = long_exit_price["close"]/long_entry_price["high"]-1-pos_ind*comm*2-pos_ind*2*slippage
short_strat_returns = short_entry_price["low"]/short_exit_price["close"]-1-short_pos_ind*2*comm*2-short_pos_ind*2*slippage

long_short_returns =short_strat_returns #pd.concat([long_strat_returns, short_strat_returns],axis=0) #
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