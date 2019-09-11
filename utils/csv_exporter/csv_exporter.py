# -*- coding: utf-8 -*-

import math
import os
import sys
sys.path.append('../../')
import openlocationcode as olc



# global constants

EARTH_RADIUS_ = 6371 # kilometers



# settings: required

# make sure this folder exists and the user running this script has write access to it
TARGET_FOLDER = '/tmp'
FILE_NAME_PREFIX = 'olc_'
FILE_NAME_SUFFIX = '.csv'

# bboxes will be created within this extent
MIN_X = 12
MIN_Y = 54
MAX_X = 12.35
MAX_Y = 54.3



# settings: optional

# bboxes will be created on this level
LEVEL = 5



# functions

# calculates the great circle distance of two geographical points
def distance_calculator(from_point_x, from_point_y, to_point_x, to_point_y):
    
  from_point_x, from_point_y, to_point_x, to_point_y = map(math.radians, [from_point_x, from_point_y, to_point_x, to_point_y])
  dlon = to_point_x - from_point_x
  dlat = to_point_y - from_point_y
  a = math.sin(dlat / 2) ** 2 + math.cos(from_point_y) * math.cos(to_point_y) * math.sin(dlon / 2) ** 2

  # return calculated distance
  return 2 * EARTH_RADIUS_ * math.asin(math.sqrt(a))



# core

# calculate the Open Location Code (OLC) level the loop will take place within if not defined in settings section
if LEVEL is not None and LEVEL in (1, 2, 3, 4, 5):
  level = LEVEL
else:
  distance = distance_calculator(MIN_X, MIN_Y, MAX_X, MAX_Y)
  if distance <= 0.8:
    level = 5
  elif distance <= 10:
    level = 4
  elif distance <= 100:
    level = 3
  elif distance <= 1000:
    level = 2
  else:
    level = 1
# calculate the OLC level resolution value
level_resolution = olc.PAIR_RESOLUTIONS_[level - 1]
# calculate the OLC code length
code_length = level * 2
# calculate the precision of level resolution
level_resolution_precision = len(str(level_resolution - int(level_resolution))[2:])
# calculate the buffer in degrees to prevent multiple encodings
buffer = 10**-(level_resolution_precision) if level_resolution_precision > 1 else 1
# calculate the number of lines (of encodings)
num_lines = int(math.ceil((round(round(MAX_Y, level_resolution_precision) - round(MIN_Y, level_resolution_precision), level_resolution_precision)) / level_resolution))
# calculate the number of rows (of encodings)
num_rows = int(math.ceil((round(round(MAX_X, level_resolution_precision) - round(MIN_X, level_resolution_precision), level_resolution_precision)) / level_resolution))
# calculate the number of bboxes (hopefully) to be created
num_bboxes = num_lines * num_rows
# get the number of digits in the number of lines (just to get nicer filenames later on...)
num_digits_in_num_lines = len(str(num_lines))

# target folder preparations
if not os.path.exists(TARGET_FOLDER):
  os.makedirs(TARGET_FOLDER)

# initial counter (needed for progress information output)
counter = 0
  
# loop through all lines
for line in range(num_lines):
  # calculate current y
  y = MIN_Y + (level_resolution * line) + buffer
  # create a new file in target folder and open it for write access
  file_name = FILE_NAME_PREFIX + str(line).rjust(num_digits_in_num_lines, '0') + FILE_NAME_SUFFIX
  temp_file = open(TARGET_FOLDER + '/' + file_name, 'w')
  # write header with column names to file
  temp_file.write('code;bbox\n')
  # loop through all rows
  for row in range(num_rows):
    # calculate current x
    x = MIN_X + (level_resolution * row) + buffer
    # encode
    code = olc.encode(y, x, code_length)
    # decode again to calculate the center pair of coordinates
    coord = olc.decode(code)
    # create new line for file
    csv = code + ';' + str(coord.longitudeLo) + ',' + str(coord.latitudeLo) + ',' + str(coord.longitudeHi) + ',' + str(coord.latitudeHi)
    # write new line to file
    temp_file.write(csv + '\n')
    # update counter (needed for progress information output)
    counter += 1
  # save and close file
  temp_file.close()
  # print progress information
  progress_percentage = round(float(counter) / float(num_bboxes) * 100, 2)
  print str(counter) + ' of ~ ' + str(num_bboxes) + ' processed (~ ' + str(progress_percentage) + ' %)'
