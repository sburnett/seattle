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
import stat

host="seattle.cs.washington.edu:8080"
url="/autograder/upload/"
allowedExts=("tar","zip","tgz")

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
    print "Error occurred while posting: %s" % sys.exc_info()[1:2][0][1]
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

#check proovided file
def checkFile(file):
  stats = os.stat(file)
  stmode = stats[stat.ST_MODE]
  if not (stmode & stat.S_IREAD):
    print "File permissions problem"
    return False
  if os.path.getsize(file)> 1048576:
    print "File size cannot exceed 1Mb"
    return False
  if file.split('.')[-1] not in allowedExts:
    print "File extension is not of an allowed type. Allowed types:"
    print allowedExts
    return False

#check provided arguments
def checkArgs(args):
  if len(args)!=4:
    return False
  if os.path.exists(args[3]) == False:
    print "File doesn't exist"
    return False
  if os.path.isdir(args[3]) == True: 
    print "Must provide a file"
    return False

#upload provided file and see results
if __name__ == "__main__":


  if checkArgs(sys.argv)==False:
    print "Invalid arguments - usage: python upload_assignment [email] [classcode] [filename]"
    exit(0)
  if checkFile(sys.argv[3])==False:
    exit(0)

  #variables and corresponding values
  var_vals=[["email",sys.argv[1]],["class_code",sys.argv[2]],["nohtml","True"]]
  
  file_to_upload=[["assignment",sys.argv[3],open(sys.argv[3]).read()]]

  #get status, reason and body of the response
  (status,reason,body)=post_to_webserver(host, url, var_vals, file_to_upload)
  if (status != 200):
    print status, reason
  print body


  
