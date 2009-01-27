"""
<Program Name>
  upload_assignment.py

<Started>
  Jan, 2008

<Author>
  sal@cs.washington.edu
  Salikh Bagaveyev

<Purpose>
  upload a file using POST to the server (for grading)

<Usage>
  provide a file to upload as an argument:
  python upload_assignment.py [classcode] [email] [filename]

  Notes: server script expects the following fields to be provided by this script:
  classcode: class code for the assignment
  email: email address of the submitter
  file: file to be submitted
  
"""

import httplib
import mimetypes
import mimetools
import os
import sys


host="192.168.0.11"
url="http://192.168.0.11/cgi-bin/upload/up.cgi"

def post_to_webserver(host, url, fields, files):
  """
  <Purpose>
    post file(s) to the server    

  <Arguments>
   url: remote script that accepts files
   fields: a list of field,value pairs 
   files: files to upload (name, filename, content)

  <Exceptions>
    HTTPrequest.request can raise exceptions which are caught and cause program to terminate with the cause message

  <Side Effects>
    Uploads files to remote computer using POST
  <Returns>
    status, reason and body of the response as strings.
  """

  content_type, body = encode_post_msg(fields, files)
  #create an http connection
  http_conn = httplib.HTTPConnection(host)
  headers = {
        'User-Agent': 'UA',
        'Content-Type': content_type
        }
  try:
    http_conn.request('POST', url, body, headers)
  except:
    print "Error occurred while posting: %s : %s" % sys.exc_info()[:2]
    sys.exit(0)
  #wait for response
  res = http_conn.getresponse()
  return res.status, res.reason, res.read()



def encode_post_msg(fields, files):
  """
  <Purpose>
   prepare content type and body for posting

  <Arguments>
   fields: a list of field,value pairs 
   files: files to upload (name, filename, content)

  <Exceptions>
   None

  <Returns>
   content type and encoded body for posting
  """

  boundary =  mimetools.choose_boundary()

  data = []
  #prepare contents
  for (key, value) in fields:
    data.append('--' + boundary)
    data.append('Content-Disposition: form-data; name="%s"' % key)
    data.append('')
    data.append(value)
  #if multiple files provided, attach them 
  for (key, filename, value) in files:
    data.append('--' + boundary)
    data.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
    contentType=mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    data.append('Content-Type: %s' % contentType)
    data.append('')
    data.append(value)
  data.append('--' + boundary + '--')
  data.append('')
  body = '\r\n'.join(data)
  content_type = 'multipart/form-data; boundary=%s' % boundary

  return content_type, body


#check provided arguments
def checkArgs(args):
  if len(args)!=4:
    return False
  if os.path.isdir(args[3]) == True: 
    print "Must provide a file"
    return False
  if os.path.getsize(args[3])> 1048576:
    print "File size cannot exceed 1Mb"
    return False
  if args[3].split('.')[-1] not in ("zip","tar"):
    print "Should provide zip or tar file"
    return False


#upload provided file and see results
if __name__ == "__main__":


  if checkArgs(sys.argv)==False:
    print "Invalid arguments - usage: python upload_assignment [classcode] [email] [filename]"
    exit(0)

  #variables and corresponding values
  var_vals=[["classcode",sys.argv[1]],["email",sys.argv[2]],["dir","images"]]
  
  file_to_upload=[["file",sys.argv[3],open(sys.argv[3]).read()]]

  #get status, reason and body of the response
  (status,reason,body)=post_to_webserver(host, url, var_vals, file_to_upload)

  print status
  print reason
  print body


  
