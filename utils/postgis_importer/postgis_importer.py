# -*- coding: utf-8 -*-

import math
import openlocationcode as olc
import os
import psycopg2



# settings

# database connection parameters
DB_HOST = '127.0.0.1'
DB_PORT = '5432'
DB_USER = 'foo'
DB_PASSWORD = 'bar'
DB_NAME = 'olc'
DB_SCHEMA = 'public'
DB_TABLE = 'code_level_5'
DB_COL_CODE = 'code'
DB_COL_SW = 'sw'
DB_COL_NE = 'ne'

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

# calculate the number of rows (of bboxes to be created)
num_rows = int(math.ceil((round(round(MAX_X, level_resolution_precision) - round(MIN_X, level_resolution_precision), level_resolution_precision)) / float(LEVEL_RESOLUTION_)))

# how many bboxes are (hopefully) to be created?
num_bboxes = num_lines * num_rows



# open database connection
db_connection = psycopg2.connect(host = DB_HOST, port = DB_PORT, dbname = DB_NAME, user = DB_USER, password = DB_PASSWORD)



# calculations

# initial counter (needed for progress information output)
counter = 0

# loop through all lines
for line in range(num_lines):

  # calculate current y
  y = float(MIN_Y) + (float(LEVEL_RESOLUTION_) * float(line))

  # open a cursor to perform database operations
  db_cursor = db_connection.cursor()

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

    # insert new line to database table
    db_cursor.execute('INSERT INTO ' + DB_SCHEMA + '.' + DB_TABLE + '(' + DB_COL_CODE + ', ' + DB_COL_SW + ', ' + DB_COL_NE + ') VALUES (%s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), ST_SetSRID(ST_MakePoint(%s, %s), 4326))', (code, str(coord.longitudeLo), str(coord.latitudeLo), str(coord.longitudeHi), str(coord.latitudeHi)))

    # update counter (needed for progress information output)
    counter += 1

  # make changes to database persistent and close database cursor
  db_connection.commit()
  db_cursor.close()

  # print progress information
  progress_percentage = round(float(counter) / float(num_bboxes) * 100, 2)
  print str(counter) + ' of ~ ' + str(num_bboxes) + ' processed (~ ' + str(progress_percentage) + ' %)'

# close database connection
db_connection.close()
