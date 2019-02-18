# -*- coding: utf-8 -*-

import math
import openlocationcode as olc
import os



# settings

# make sure this folder exists and the user running this script has write access to it
TARGET_FOLDER = '/tmp'
FILE_NAME_PREFIX = 'olc_'
FILE_NAME_SUFFIX = '.csv'

# bboxes will be created for this Open Location Code (OLC) level
LEVEL = 5

# bboxes will be created within this extent
MIN_X = 12
MIN_Y = 54
MAX_X = 12.35
MAX_Y = 54.3



# global constants

# resolution value in degrees for level configured above in the OLC encoding
LEVEL_RESOLUTION_ = olc.PAIR_RESOLUTIONS_[LEVEL - 1]



# global variables

# precision of level resolution
level_resolution_precision = len(str(LEVEL_RESOLUTION_ - int(LEVEL_RESOLUTION_))[2:])
  
# calculate the number of lines (of bboxes to be created)
num_lines = int(math.ceil((round(round(MAX_Y, level_resolution_precision) - round(MIN_Y, level_resolution_precision), level_resolution_precision)) / float(LEVEL_RESOLUTION_)))

# how many digits in the number of lines? just to get nicer filenames later on...
num_digits_in_num_lines = len(str(num_lines))

# calculate the number of rows (of bboxes to be created)
num_rows = int(math.ceil((round(round(MAX_X, level_resolution_precision) - round(MIN_X, level_resolution_precision), level_resolution_precision)) / float(LEVEL_RESOLUTION_)))

# how many bboxes are (hopefully) to be created?
num_bboxes = num_lines * num_rows



# target folder preparations

if not os.path.exists(TARGET_FOLDER):
  os.makedirs(TARGET_FOLDER)



# calculations

# initial counter (needed for progress information output)
counter = 0

# loop through all lines
for line in range(num_lines):

  # calculate current y
  y = float(MIN_Y) + (float(LEVEL_RESOLUTION_) * float(line))

  # create a new file in target folder and open it for write access
  file_name = FILE_NAME_PREFIX + str(line).rjust(num_digits_in_num_lines, '0') + FILE_NAME_SUFFIX
  temp_file = open(TARGET_FOLDER + '/' + file_name, 'w')

  # write header with column names to file
  temp_file.write('code;bbox\n')

  # loop through all rows
  for row in range(num_rows):

    # calculate current x
    x = float(MIN_X) + (float(LEVEL_RESOLUTION_) * float(row))

    # get the full Plus code related to current x and y
    code = olc.encode(y, x)

    # decode the Plus code to calculate the bbox
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
