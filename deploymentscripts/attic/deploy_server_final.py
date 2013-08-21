"""
<Program Name>
  deploy_server_final.py

<Started>
  July 2009

<Author>
  n2k8000@u.washington.edu
  Konstantin Pik

<Purpose>
  This is a fully automated webserver that handles only certain web requests.  The server assumes files exist
  in the locations that they're supposed to exist, and the files are placed there by make_summary.py which in turn
  draws its files from deploy_main and related scripts.


<Usage>
  python deploy_server_final.py
  
  The deploy_server_monitor.py file should start and stop the server for you, so you shouldn't have to
  manage the server by yourself.
"""

import os
import time

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer


class RequestHandler(BaseHTTPRequestHandler):
  """
  <Purpose>
    This class is the custom request handler that we'll have our server use.

  <Arguments>
    BaseHTTPRequestHandler:
      The requesthandler object
  """
  
  
  def do_GET(self):
    """
    <Purpose>
      Class method to handle GET requests.

    <Arguments>
      self:
        this is the request object.

    <Exceptions>
      any type of error while sending back a reply.

    <Side Effects>
      None.

    <Returns>
      None.
    """
    try:
      
      # parse the requested page and see if it's valid
      parse_status, explanation_str = self.parse_header(self.path)
      
      # parse_status:
      # -1: error
      # 0:  /log/* request
      # 1:  /detailed/node/timestamp request
      print str(self.parse_header(self.path))
      
      explanation_str = str(explanation_str)
      
      # error
      if parse_status == -1:
        # invalid header, close the connection and die but notify user
        self.send_response(200)
        self.send_header('Content-type',	'text/html')
        self.end_headers()
        self.wfile.write('Invalid request ('+explanation_str+')')
        print '-1'
        return
      
      # 1:  /detailed/node/timestamp request
      elif parse_status == 1:
        print '1'
        # just need to respond with the file that's contained in explanation_str
        # and once we verify that it exists, we're golden
        
        # path to the "detailed" file
        file_path = explanation_str
        
        if os.path.isfile(file_path):
          try:
            # TODO: make HTML here to nav around previous node things
            detailed_file_handle = open(file_path, 'r')
            self.send_response(200)
            self.send_header('Content-type',	'text/plain')
            self.end_headers()            
            self.wfile.write(detailed_file_handle.read())
            detailed_file_handle.close()
            return
          except Exception, e:
            print 'Error while sending detailed log file'
            print e
            return
        else:
          self.send_response(200)
          self.send_header('Content-type',	'text/html')
          self.end_headers()
          self.wfile.write('Invalid file request')
          return
          
      # 0:  /log/* request
      elif parse_status == 0:
        print '0'
        # request was successfull, we just want the filename from index
        log_index = explanation_str
        
        success_status, log_filename = self.get_filename_from_index(log_index)
        
        if success_status == -1:
          # some kind of error of which the description is stored in log_filename
          #sockobj.send('The server encountered an error opening the file, please'+\
          #  ' try your request again')
          self.send_response(200)
          self.send_header('Content-type',	'text/html')
          self.end_headers()            
          self.wfile.write('The server encountered an error opening the file, please'+\
            ' try your request again')
          return
        
        # the file exists!
        # just dump the file at this point, and then...
        
        # send the HTML file
        self.send_response(200)
        self.send_header('Content-type',	'text/html')
        self.end_headers()
        self.send_html_file(log_filename, log_index)
        return

      # invalid type
      else:
        self.send_response(200)
        self.send_header('Content-type',	'text/html')
        self.end_headers()
        self.wfile.write('Invalid request type 2')
        return
        
    except IOError:
      self.send_error(404,'File Not Found: %s' % self.path)
   
    return

    
    
  def do_POST(self):
    # POST requests are not handled by our server.  just let the user know that.
    try:
      self.send_response(200)
      self.send_header('Content-type',	'text/html')
      self.end_headers()
      self.wfile.write('Invalid request: POST is not supported')
      
    except :
      pass

      

  def make_link_to(self, index, caption):
    """
    <Purpose>
      This function makes a link to the index with a caption

    <Arguments>
      self:
        this object
      index: (expected int, but can be str)
        the index to link to (relative to this one, 0 is most recent)
      caption:
        the caption for that index
        

    <Exceptions>
      None.

    <Side Effects>
      None.

    <Returns>
      HTML to be inserted and created for page by page navigation
    """
    
    # index is an int
    return '<a href="/log/'+str(index)+'"> '+caption+' '+str(index)+'</a>'

    
    
  def get_next_index(self, current_index_string):
    """
    <Purpose>
      Gets the 'next' index to grab.

    <Arguments>
      self:
        this requesthandler object
      current_index_string:
        the string representation of a number: current index

    <Exceptions>
      None.

    <Side Effects>
      None.

    <Returns>
      Integer.  The next index in the series.
    """
    # current index is a string, so cast to int
    current_index = int(current_index_string)

    return current_index+1


    
  def get_previous_index(self, current_index_string):
    """
    <Purpose>
      Gets the 'previous' index to grab.

    <Arguments>
      self:
        this requesthandler object
      current_index_string:
        the string representation of a number: current index

    <Exceptions>
      None.

    <Side Effects>
      None.

    <Returns>
      Integer.  The previous index in the series.
    """
    # current index is a string, so cast to int
    current_index = int(current_index_string)

    return current_index-1

    
    
  def print_navigation(self, current_index):
    """
    <Purpose>
      Prints the navigation on the current page.

    <Arguments>
      self:
        this requesthandler object
      current_index:
        The current index that this person is on.

    <Exceptions>
      None.

    <Side Effects>
      None.

    <Returns>
      String. HTML representation of the navigation.
    """
    # current_index: current index
    
    # the html string we're going to build up
    html = ""
    
    html+='<table width="100%"><tr>'
    
    # returns some HTML that are the navigation links at the bottom of the page
    previous_index = self.get_previous_index(current_index)
    
    if previous_index != -1:
      # not empty, so make a link
      html += '<td align="center">'
      previous_link = self.make_link_to(previous_index, 'Previous')
      html += previous_link+'</td>'
      
    next_index = self.get_next_index(current_index)
    
    if next_index != -1:
      html += '<td align="center">'
      next_link = self.make_link_to(next_index, 'Next')
      html += next_link+'</td>'

    html += '</table>'
    return html

    

  def read_whole_file(self, file_handle):
    """
    <Purpose>
      Reads in a whole file given a file handle

    <Arguments>
      self:
        this requesthandler object
      file_handle
        the file handle of the file to read

    <Exceptions>
      None.

    <Side Effects>
      None.

    <Returns>
      String. The file contents as string.
    """
    # reads in a whole file given a file handle
    
    temp_str = ""
    for each_line in file_handle.xreadlines():
      temp_str += each_line
    return temp_str
  
  
  
  def send_html_file(self, html_fn, log_index):
    """
    <Purpose>
      Grabs the html_fn (which is the file autogenerated by make_summary.py) and
      sends it using the built-in methods in self.

    <Arguments>
      self:
        this requesthandler object
      html_fn:
        the file name of the html file to send
      log_index:
        log index of the html_fn so that we can print the navigation at the bottom of the page

    <Exceptions>
      File related exceptions.
      Exception sending response.      

    <Side Effects>
      None.

    <Returns>
      
    """
    try:
      html_handle = open(html_fn, 'r')
      
      # read in the html_fil
      file_data = self.read_whole_file(html_handle)      
      html_handle.close()
      # send the file, except add the nav links at the bottom
      self.wfile.write(file_data.replace('</html>', self.print_navigation(log_index)+'</html>'))
      
    except Exception, e:
      self.wfile.write('Server-side error while reading file ('+str(e)+')')
      
    return
      
      
      
  def parse_header(self, header):
    """
    <Purpose>
      This function parser the 'header' which is a simple string of what we want to get

    <Arguments>
      self:
        this object
      header:
        the request string (not the full http header)

    <Exceptions>
      None.

    <Side Effects>
      None.

    <Returns>
      returns tuples (SuccessStatus, Explanation)
    """
    # 
    
    # this is what the line'll look like:
    # e.g.: /logs/1
    # e.g.: /detailed/host/timestamp

    # get index of first slash
    first_slash = header.index('/')
    
    
    # splice the string now and remove any spaces
    requested_folder = header.strip('/')
    
    # check if it's just a slash
    if not requested_folder:
      # return a 0 meaning we want the latest log file
      return (0, 0)
    else:
      # check that it's a valid request
      detailed_request = requested_folder.split('/')
      # detailed_request should be of form /log/* where * is a number
      # two types of requests:
      # type 1: /log/* where * is a number
      # type 2: /detailed/node_name/timestamp
      #       node_name: node name
      #       timetamp is the timestamp of the run
      
               
      if len(detailed_request) == 2:
        # type 1 request
        # first entry is '' since there's a leading '/'
        if detailed_request[0] == 'log':
          # now get a valid number for a folder request
          try:
            log_number = int(detailed_request[1])
          except Exception, e:
            print "Error obtaining log (request: "+requested_folder+")"
            return (-1, str(e))
          else:
            return (0, log_number)
        else:
          return (-1, 'Invalid request (len 2)')
      elif len(detailed_request) == 3:
        # type 2 request
        if detailed_request[0] == 'detailed':
          nodename = detailed_request[1]
          timestamp = detailed_request[2]
          # verify that timestamp is a valid #
          try:
            timestamp_int = int(timestamp)
          except ValueError, ve:
            print 'Invalid timestamp requested, '+timestamp
            print ve
            return (-1, 'Invalid timestamp')
          else:
            # return the filepath as our response
            return (1, './detailed_logs/'+nodename+'/'+timestamp)
            
            
        else:
          return (-1, 'Invalid request (len 3)')
        
      else:
        # invalid!
        return (-1, 'Invalid detailed log request ('+str(detailed_request)+')')
        

        
  def get_filename_from_index(self, log_index, depth = 5):
    """
    <Purpose>
      Gets the nth (log_index) filename from the master.log file

      master files keeps track of the fn's that we have, one on each line
      newest ones are at the end.
    <Arguments>
      self:
        this object
      log_index:
        the requested log_index:
      depth:
        not to be set manually. will retry this many times to get a filename.

    <Exceptions>
      File related errors (read/write).

    <Side Effects>
      None.

    <Returns>
      Tuple.
      On error:
        (-1, Error description string)
      On success:
        (1, filename)
    """

    try:
      
      if os.path.isfile('./master.log'):
        #global_lock.acquire()
        master_files_handle = open('./master.log', 'r')
        all_lines = master_files_handle.readlines()
        #global_lock.release()
      else:
        return_value = (-1, 'No logs to report from yet')
        return return_value
      # if 0, then that's the "most recent"
      

      # default value
      return_value = (-1, 'No Valid Page')
      
      if str(log_index) == '0':
        return_value = (1, all_lines[-1].strip('\n'))
      else:
        return_value = (1, all_lines[-(int(log_index) % len(all_lines)) - 1].strip(' \n'))
      master_files_handle.close()    
      
    except Exception, e:
      print 'Error in get_filename_from_index'
      print e
      return (-1, e)
    else:
      # means it's blank..
      # the depth variable is so that we don't infinitely hang
      if not return_value[1] and depth > 0:
        new_index_int = (int(log_index)-1)
        print 'Redirecting to '+str(new_index_int)+' with depth '+str(depth)
        return_value = self.get_filename_from_index(str(new_index_int), depth - 1)
      return return_value



def main():
  # boot up our server on port 4444 and set our custom class
  # as the request handler for it.
  try:
    server = HTTPServer(('', 4444), RequestHandler)
    print 'started httpserver...'
    server.serve_forever()
  except Exception, e:
    print e
  
  
  

if __name__ == '__main__':
  main()

