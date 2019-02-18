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
MIN_X = 10.0
MIN_Y = 52.5
MAX_X = 15
MAX_Y = 55



# global constants

# resolution value in degrees for level configured above in the OLC encoding
LEVEL_RESOLUTION_ = olc.PAIR_RESOLUTIONS_[LEVEL - 1]



# global variables
  
# calculate the number of lines (of bboxes to be created)
num_lines = int(math.ceil((float(MAX_Y) - float(MIN_Y)) / float(LEVEL_RESOLUTION_)))

# how many digits in the number of lines? just to get nicer filenames later on...
num_digits_in_num_lines = len(str(num_lines))

# calculate the number of rows (of bboxes to be created)
num_rows = int(math.ceil((float(MAX_X) - float(MIN_X)) / float(LEVEL_RESOLUTION_)))

# how many bboxes are (hopefully) to be created?
num_bboxes = num_lines * num_rows



# target folder preparations

if not os.path.exists(TARGET_FOLDER):
  os.makedirs(TARGET_FOLDER)



# calculations

# initial counter (needed for progress information output)
counter = 1

# loop through all lines (0-based, therefore 1 more than number of lines)
for line in range(num_lines + 1):

  # calculate current y
  y = MIN_Y + (LEVEL_RESOLUTION_ * line)

  # create a new file in target folder and open it for write access
  file_name = FILE_NAME_PREFIX + str(line).rjust(num_digits_in_num_lines, '0') + FILE_NAME_SUFFIX
  temp_file = open(TARGET_FOLDER + '/' + file_name, 'w')

  # write header with column names to file
  temp_file.write('code;bbox\n')

  # loop through all rows (0-based, therefore 1 more than number of rows)
  for row in range(num_rows + 1):

    # calculate current x
    x = MIN_X + (LEVEL_RESOLUTION_ * row)

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
