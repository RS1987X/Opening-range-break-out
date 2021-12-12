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

evo_data = pd.read_csv('OMXSTO_DLY_EVO, 15.csv')
evo_data = evo_data['time;open;high;low;close;VWAP;Upper Band;Lower Band;Volume;Volume MA'].str.split(";",expand=True)
evo_data = evo_data.rename(columns={0:"DateTime", 1:"Open", 2:"High", 3:"Low", 4:"Close", 5:"VWAP", 6:"Upper Band", 7:"Lower Band", 8:"Volume", 9:"Volume MA"})
evo_data = evo_data[["DateTime","Open","High", "Low", "Close","Volume"]]



time_offset_removed =  evo_data["DateTime"].str[:-6]
only_date_part = evo_data["DateTime"].str[:-15]



#evo_data = evo_data.set_index("DateTime")
#
#evo_data["DateTime"] = 



#datetime.strptime(evo_data.index[0],'%Y-%m-%dT%H:%M:%S').time()

#evo_data.groupby('DateTime')["High"].transform("max")

#


#dates = evo_data.index.str.split(",")
#yourdate = parser.parse(dates)