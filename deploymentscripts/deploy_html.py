"""
<Program Name>
  deploy_html.py

<Started>
  June 2009

<Author>
  n2k8000@u.washington.edu
  Konstantin Pik

<Purpose>
  The purpose of this file is to seperate any html generation required
  for the webserver files.  This module just provides methods for creating
  html pages and html tables from dicts and arrays.  See method details for 
  more information.


<Usage>
  This is not to be launched as an independent file, but its methods are to be used
  as helper methods.
"""


import deploy_main

import time
import os


"""
Public functions:
  html_add_to_top
  
"""
# maps different warning levels to colors
colors_table = ['Red', 'Gold', 'LightGreen', 'White']
colors_map = {'Error' : 'Red', 'Success': 'LightGreen',
  'Warning' : 'Gold', 'SmallError' : 'Yellow', 'Normal' : 'White'}

  
  
# the acceptable node versions
target_node_versions = ['0.1h', '0.1i', '0.1j']



def get_colors_map():
  # helper method
  return colors_map

  
  
def add_html_column_names(column_names):
  """
  <Purpose>
    Creates a row in a table, but assumes them to be column names and thus
    makes the entries bold.
     
  <Arguments>
    column_names:
      an array of string elements to be used as column names. This string 
      may contain HTML.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    The HTML string for the row.
  """

  # create a row
  temp_html = add_row()
  # add a cell for each entry
  for each_title in column_names:
    # and make it bold
    temp_html += add_cell('<b>'+str(each_title)+'</b>')

  # close the row
  temp_html += close_row()
  return temp_html

  
  
def start_html():
  # returns an HTML header
  return '<html>'

  
  
def close_html():
  # closes the HTML and returns string
  return '</html>'
  
  
  
def create_table():
  # creates the main entry in a table, returns HTML string
  return '<table border="1">'

  
  
def add_cell(cell_value, cell_bg_color = None):
  """
  <Purpose>
    Returns the HTML for a cell (html TD element).
     
  <Arguments>
    cell_value:
      1.  Can be a simple string that's the cell value (may contain HTML)
      2.  Can be a tuple in which case the tuple is of form (cell_value, color)
          cell_value can once again be a string/html and color is the bg color to use.
    cell_bg_color:
      The bg color to use for the cell.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    String. HTML for the newly created cell.
  """

  # check the type of the cell_value
  if type(cell_value) == type(()):
    cell_bg_color = cell_value[1]
    cell_value = cell_value[0]

  # use a bg color if one is set, and make sure to alight the text to the 
  # middle of the cell
  if cell_bg_color:
    cell_html = '<td bgcolor="'+cell_bg_color+'" valign="center">'+str(cell_value)+'</td>'
  else:
    cell_html = '<td valign="center">'+str(cell_value)+'</td>'
  
  return cell_html

  
  
def add_row_of_elements(element_array):
  # see below
  return add_node_row(element_array)


  
def add_node_row(iterable_item_list):
  """
  <Purpose>
    Takes in an iterable type, and for each item in that list it'll make a cell
    and return the HTML for that row of elements.
    
    Basically makes a row from the list.
     
  <Arguments>
    iterable_item_list:
      Something that can be iterated over.  Should contain string-compatible values as
      each value will be given its own cell.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    String. HTML for the row created from the list.
  """


  # calls add_row and creates a row with the information (with cells)
  row_html = add_row()
  
  for each_item in iterable_item_list:
    row_html += add_cell(each_item)
    
  # close the row.
  row_html += close_row()
  
  return row_html
  
  
  
def add_row():
  # creates a row element.
  return '<tr>'

  
  
def html_add_to_top(html_fn, html_to_add):
  """
  <Purpose>
    Opens a file and adds some content to the top of the file.
     
  <Arguments>
    html_fn:
      the name of the html file.  note: this MUST be an html file.
    html_to_add:
      The HTML that'll be added to the top of the file.
    
  <Exceptions>
    File reading/writing related exceptions.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  try:
    # get a handle on the file
    html_filehandle = open(html_fn, 'r')
    
    # read the whole thing in
    html_file_string = read_whole_file(html_filehandle)
    html_filehandle.close()
    
    # now after closing the file, we'll add our html
    html_file_string = html_file_string.replace('<html>', '<html><br>'+html_to_add+'<br>')
    
    # open the file and overwrite it with the new data
    html_file_handle = open(html_fn, 'w+')
    html_file_handle.write(html_file_string)
    html_file_handle.close()
    
  except Exception, e:
    print e
  

  
def close_row():
  # close the row
  return '</tr>'

  
  
def close_table():
  # HTML to close the table
  return '</table>'

  
  
def generate_uniq_fn():
  """
  <Purpose>
    Generates a uniq filename based on the current time.
     
  <Arguments>
    None.
    
  <Exceptions>
    None

  <Side Effects>
    None.

  <Returns>
    Tuple.  (htmlsummary.[time.time()], time.time())
      The time.time() is stored in a variable so it'll be the same time.
  """
  current_time = int(time.time())
  return ("htmlsummary."+str(current_time), str(current_time))

  

def read_whole_file(file_handle):
  """
  <Purpose>
    Reads in a whole file given a file handle and returns the file as string.
     
  <Arguments>
    file_handle:
      the file_handle of the file to read
    
  <Exceptions>
    None

  <Side Effects>
    None.

  <Returns>
    String. The contents of the file to which we have a handle to as a string.
  """
  temp_str = ""
  for each_line in file_handle.xreadlines():
    temp_str += each_line
  return temp_str



def make_link_to_detailed(node_name, html_fn):
  """
  <Purpose>
    Generates a link to the detailed node data.
     
  <Arguments>
    node_name:
      The name of the node
    html_fn:
      The html file name which has the following format: htmlsummary.[timestamp]
    
  <Exceptions>
    None

  <Side Effects>
    None.

  <Returns>
    String. HTML that's a link to the detailed log for this node.
  """
  
  # split up the html_fn to get the timestamp
  junk, sep, timestamp = html_fn.rpartition('.')
  
  # put it all together and return the html string
  return '<a href="/detailed/'+node_name+'/'+timestamp+'" target="_blank">Details</a>'



def format_text_for_html(text):
  # basically replaces \n's with <br>'s
  return str(text).replace('\n', '<br>')

  
  
def html_table_from_dict2(table_dict, table_headers):
  """
  <Purpose>
    Converts a dict to an HTML table.  The dict is assumed to have
    1:1 mapping where each key maps to an array.  The key is then
    created as the first element in that row.  The table_headers is assumed to
    be the size of 1 + len(array) where each array size is expected to be the same
    for each key.
     
  <Arguments>
    table_dict:
      Dict that has the following format:
        {"stringkey1" : [el_1, el_2, el_n], "stringkey2" : [el_1, el_2, el_n], ... }
      or
        {"stringkey1" : "string1", "stringkey2" : "stringx", ... }
    table_headers:
      List (expected array, but in theory could be any iterable) that is of length
      n + 1 where n is the number of elements in the array of stringkeyX (all should be
      same size).
    
  <Exceptions>
    None

  <Side Effects>
    None.

  <Returns>
    HTML for a complete table created from the dict with the headers from the list.
  """
  
  # key -> array. Value printed as string.
  html_table = create_table()
  
  html_table += add_html_column_names(table_headers)
  
  # for every key grab the elements
  for each_key in table_dict:
  
    # create a row for this key.
    html_table += add_row()
  
    # add the value of the key as the first element
    html_table += add_cell(each_key)
    
    # if we map to an array
    if type(table_dict[each_key]) == type([]):
      # then dump each element of that array to its own cell
      for each_element in table_dict[each_key]:
        html_table += add_cell(each_element)
    else:
      # otherwise just dump whatever we map to (hopefully a string) to the cell
      html_table += add_cell(each_key)
    
  # close the table
  html_table += close_table()
  
  return html_table
  


def html_table_from_dict(table_dict, table_headers):
  """
  <Purpose>
    Converts a dict to a simple, two column HTML table.  Simple mapping of 
    Key->Value where value is a string. The headers for the table are defined 
    in table_headers
     
  <Arguments>
    table_dict:
      Dict that has the following format:
        {"stringkey1" : "string1", "stringkey2" : "stringx", ... }
    table_headers:
      List (expected array, but in theory could be any iterable) that is of length
      n + 1 where n is the number of elements in the array of stringkeyX (all should be
      same size).
    
  <Exceptions>
    None

  <Side Effects>
    None.

  <Returns>
    HTML for a complete table created from the dict with the headers from the list.
  """
  # key -> value. Value printed as string
  html_table = create_table()
  
  # generate the column headers
  html_table += add_html_column_names(table_headers)
  
  # for each key
  for each_key in table_dict:
    # create a row
    html_table += add_row()
    
    # add the keyname as the first element in the row
    html_table += add_cell(each_key)
    
    # add whatever the key maps to as the second element in the row
    html_table += add_cell(table_dict[each_key])
    
    # close the row
    html_table += close_row()
  
  # close the table
  html_table += close_table()
  
  return html_table
  
  

def html_table_from_array(table_array):
  """
  <Purpose>
    Convert an array to a table
     
  <Arguments>
    table_array;
      an array of the following form:
      table_array[0] maps to an array where each element is a header
      table_array[n > 0] maps to an array and each element in that array will be a row
      
      assumes table_array is a square array.
    
  <Exceptions>
    None

  <Side Effects>
    None.

  <Returns>
    HTML for a complete table created from the array.
    
  """

  # get the headers
  table_headers = table_array[0]
  
  # create the table
  html_table = create_table()
  
  # create the column headers
  html_table += add_html_column_names(table_headers)

  # for the length of the table (-1 is for the 0th index which is the headers)
  for i in range(len(table_array) - 1):
    # (+1 is to offset for the column headers @ index 0)
    html_table += add_row_of_elements(table_array[i+1])

  # close the table
  html_table += close_table()
  
  return html_table

  

def html_write(html_fn, html_to_write):
  """
  <Purpose>
    Appends (or creates) to html_fn the html_to_write.
     
  <Arguments>
    html_fn:
      the name of the html file to be written to (will append)
    html_to_write:
      The HTML that'll be appended
    
  <Exceptions>
    File reading/writing related exceptions.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  
  try:
    # get a file handle to the html_file
    html_file_handle = open(html_fn, 'a')
    
    # opens up master.log and appends the file name of this file to it
    master_handle = open('./master.log', 'a')
    master_handle.write('\n'+html_fn)
    master_handle.close()
   
    # writes the html file.
    html_file_handle.write(start_html())
    html_file_handle.write(html_to_write)
    html_file_handle.write(close_html())
    
    html_file_handle.close()
    
  except Exception, e:
    print 'Exception in html_write'
    print e