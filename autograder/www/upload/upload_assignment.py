"""
<Program Name>
  upload.py

<Started>
  Jan, 2008

<Author>
  sal@cs.washington.edu
  Salikh Bagaveyev

<Purpose>
  upload a file using POST to the server (for grading)

<Usage>
  provide a file to upload as an argument
"""

import httplib
import mimetypes
import mimetools
import sys

"""
post file(s) to the server
url: remote script that accepts files
fields: a list of field,value pairs 
files: files to upload (name, filename, content)

"""
def post(host, url, fields, files):
  content_type, body = encode(fields, files)
  #create an http connection
  http_conn = httplib.HTTPConnection(host)
  headers = {
        'User-Agent': 'UA',
        'Content-Type': content_type
        }
  http_conn.request('POST', url, body, headers)
  #wait for response
  res = http_conn.getresponse()
  return res.status, res.reason, res.read()


#get content type and body for posting
def encode(fields, files):

  boundary =  mimetools.choose_boundary()

  data = []
  #prepare contents
  for (key, value) in fields:
    data.append('--' + boundary)
    data.append('Content-Disposition: form-data; name="%s"' % key)
    data.append('')
    data.append(value)
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

#upload provided file and see results
def pst():
  nameval=[["dir","images"]]
  nfv=[["file",sys.argv[1],open(sys.argv[1]).read()]]
  (a,b,c)=post("192.168.0.11","http://192.168.0.11/cgi-bin/upload/up.cgi",nameval,nfv)
  print a
  print b
  print c

pst()
  
