#!/usr/bin/env python

import os
import sys
import numpy
import math 
from hampel import *
from pylab import *
from copy import deepcopy
from optparse import OptionParser
# Savitzky-Golay filte
from scipy.signal import savgol_filter
from astropy.time import Time
from astropy.timeseries import TimeSeries
import astropy.units as u

#from datetime import datetime


def getdata( filename ):
        text = open(filename, 'r').readlines()
        L = len(text)
        i = 0
        # skip over all stuff before actual data
#       reference time for rel_time=0: year,month,day,hr,min,sec  2022 8 8 14 0 0.0
        while(text[i][0:14] != 'reference time'):
           i = i+1
        info = text[i].split()
        sec = str(info[-1])
        min = str(info[-2])
        hour = str(info[-3])
        day = str(info[-4])
        month = str(info[-5])
        year = str(info[-6])
        time_string = year + '-' + month + '-' + day + 'T' + hour + ':' + min + ':' + sec
        print('time_string', time_string)
        iso_time = Time(time_string, format='isot', scale='utc')
        print('starting iso_time', iso_time)
        ref_time = iso_time
        while(text[i][0:13] != 'seq  rel_time'):
           i = i+1
        rm = []
        rel_time = []
        rm_error=[]
        start = i+1
        # get actual data
        print('size of text', len(text))
        for i in range( start,len(text)):
          try:
            info = text[i].split()
            if int(info[2]) == 0:
              elev = float(info[5])
              if elev >= 15.0:
                latest = ref_time + float(info[3]) / 3600 * u.hour
                rel_time.append(latest)
                rm_val = float(info[8])
                rm.append(rm_val)
                try:
                 error_ratio = rm_val * float(info[10]) / float(info[7])
                 rm_error.append(error_ratio)
                except:
                  continue
          except:
            pass
# Creating an numpy array by specifying the data type as datetime
        datetime_list = [t.datetime for t in rel_time]
        datetime_arr = numpy.array(datetime_list)
        rm_arr = numpy.array(rm)
        error_array = numpy.array(rm_error)
        return rel_time,datetime_arr, rm_arr, error_array, latest, ref_time

def main( argv ):
  RM = True
  parser = OptionParser(usage = '%prog [options] ')
  parser.add_option('-f', '--file', dest = 'filename', help = 'Name of ALbus file to be processed  (default = None)', default = None)
  parser.add_option('-s', '--smooth', dest = 'smooth', help = 'Type of smoothing, sg , h, or None  (default = None)', default = None)
  (options,args) = parser.parse_args()
  filename = options.filename
  print('processing ALBUS file ', filename)
  smoothing = str(options.smooth).lower()
  rel_time,times, y_data, errors, latest, ref_time  = getdata(filename)
  ts = TimeSeries(time=rel_time)
  ts['albus_RM'] = y_data
  ts['albus_errors'] = errors
# don't write out a time series file for the moment
# ts.write('albus_time_series', format='ascii.ecsv', overwrite=True)
# Savitzky-Golay filter
  if smoothing == 'sg':
    print('Doing Savitzky-Golay smoothing')
    y_data = savgol_filter(y_data, 7, 1)
  elif smoothing == 'h':
    print('Doing Hampel filtering')
    filtered = hampel(y_data, 5, 4)
    y_data = hampel(filtered, 10, 1)
  
# Create the plot
  fig, ax1 = plt.subplots(figsize=(10, 6))

# Plot data with error bars
  plt.xticks(rotation=20)
  ax1.errorbar(times, y_data, yerr=errors, fmt='ro', label='RM Data with Errors')
  ax1.set_xlabel("Time (UTC)")
  ax1.set_ylabel('RM (rad/m^2)')
  ax1.set_title('RM as a function of time')
  ax1.grid(True)
  ax1.legend()

# Create a second x-axis for Julian date
  ax2 = ax1.twiny()
  ax2.set_xlabel("Time (Modified Julian Date)")
  ax2.set_xlim(ax1.get_xlim())
  ax2.set_xticks(ax1.get_xticks())
  ax2.set_xticklabels([f"{t:.2f}" for t in Time(ax1.get_xticks(), format='plot_date').mjd])

  fig.tight_layout()

  plot_file =  filename + '_rm_plot'
# title_string = 'RM as a function of time'
# title(title_string)
  grid(True)

# remove and "." in this string
  pos = plot_file.find('.')
  if pos > -1:
    plot_file = plot_file.replace('.','_')
  plt.savefig(plot_file)
  plt.show()


#=============================
# argv[1]  incoming ALBUS results file 
if __name__ == "__main__":
  main(sys.argv)
