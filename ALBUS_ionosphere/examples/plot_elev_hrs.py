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
import astropy.units as u

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
        elev_val = []
        rel_time = []
        start = i+1
        # get actual data
        for i in range( start,len(text)):
          try:
            info = text[i].split()
            if int(info[2]) == 0:
              elev = float(info[5])
              latest = ref_time + float(info[3]) / 3600 * u.hour
              rel_time.append(latest)
              elev_val.append(elev)
          except:
            pass
# Creating an numpy array by specifying the data type as datetime
        datetime_list = [t.datetime for t in rel_time]
        datetime_arr = numpy.array(datetime_list)
        elev_arr = numpy.array(elev_val)
        return datetime_arr, elev_arr, latest, ref_time

def main( argv ):
  RM = True
  parser = OptionParser(usage = '%prog [options] ')
  parser.add_option('-f', '--file', dest = 'filename', help = 'Name of ALbus file to be processed  (default = None)', default = None)
  parser.add_option('-s', '--smooth', dest = 'smooth', help = 'Type of smoothing, sg , h, or None  (default = None)', default = None)
  (options,args) = parser.parse_args()
  filename = options.filename
  print('processing ALBUS file ', filename)
  smoothing = str(options.smooth).lower()
  times, y_data, latest, ref_time  = getdata(filename)

# Create the plot
  fig, ax1 = plt.subplots(figsize=(10, 6))

# Plot data with error bars
  plt.xticks(rotation=20)
  ax1.plot(times, y_data,'ro')
  ax1.set_xlabel('UT (hours)')
  ax1.set_ylabel('Elevation(degrees)')
  ax1.set_title('Elevation as a function of time')
  ax1.grid(True)

# Create a second x-axis for Julian date
  ax2 = ax1.twiny()
  ax2.set_xlabel("Time (Modified Julian Date)")
  ax2.set_xlim(ax1.get_xlim())
  ax2.set_xticks(ax1.get_xticks())
  ax2.set_xticklabels([f"{t:.2f}" for t in Time(ax1.get_xticks(), format='plot_date').mjd])

  fig.tight_layout()

  plot_file =  filename + '_elevation_plot'
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
