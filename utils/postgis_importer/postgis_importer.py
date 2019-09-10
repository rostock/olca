# -*- coding: utf-8 -*-

import math
import os
import psycopg2
import sys
sys.path.append('../../')
import openlocationcode as olc



# settings: required

# database connection parameters
DB_HOST = '127.0.0.1'
DB_PORT = '5432'
DB_USER = 'foo'
DB_PASSWORD = 'bar'
DB_NAME = 'olc'
DB_SCHEMA = 'public'
DB_TABLE = 'codes'
DB_COL_CODE = 'code'
DB_COL_SW = 'sw'
DB_COL_NE = 'ne'

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
  if distance <= 0.75:
    level = 5
  elif distance <= 7.5:
    level = 4
  elif distance <= 150:
    level = 3
  elif distance <= 1500:
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

# open database connection
db_connection = psycopg2.connect(host = DB_HOST, port = DB_PORT, dbname = DB_NAME, user = DB_USER, password = DB_PASSWORD)

# initial counter (needed for progress information output)
counter = 0
  
# loop through all lines
for line in range(num_lines):
  # calculate current y
  y = MIN_Y + (level_resolution * line) + buffer
  # open a cursor to perform database operations
  db_cursor = db_connection.cursor()
  # loop through all rows
  for row in range(num_rows):
    # calculate current x
    x = MIN_X + (level_resolution * row) + buffer
    # encode
    code = olc.encode(y, x, code_length)
    # decode again to calculate the center pair of coordinates
    coord = olc.decode(code)
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
