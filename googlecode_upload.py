#!/usr/bin/env python
#
# Copyright 2006, 2007 Google Inc. All Rights Reserved.
# Author: danderson@google.com (David Anderson)
#
# Script for uploading files to a Google Code project.
#
# This is intended to be both a useful script for people who want to
# streamline project uploads and a reference implementation for
# uploading files to Google Code projects.
#
# To upload a file to Google Code, you need to provide a path to the
# file on your local machine, a small summary of what the file is, a
# project name, and a valid account that is a member or owner of that
# project.  You can optionally provide a list of labels that apply to
# the file.  The file will be uploaded under the same name that it has
# in your local filesystem (that is, the "basename" or last path
# component).  Run the script with '--help' to get the exact syntax
# and available options.
#
# Note that the upload script requests that you enter your
# googlecode.com password.  This is NOT your Gmail account password!
# This is the password you use on googlecode.com for committing to
# Subversion and uploading files.  You can find your password by going
# to http://code.google.com/hosting/settings when logged in with your
# Gmail account. If you have already committed to your project's
# Subversion repository, the script will automatically retrieve your
# credentials from there (unless disabled, see the output of '--help'
# for details).
#
# If you are looking at this script as a reference for implementing
# your own Google Code file uploader, then you should take a look at
# the upload() function, which is the meat of the uploader.  You
# basically need to build a multipart/form-data POST request with the
# right fields and send it to https://PROJECT.googlecode.com/files .
# Authenticate the request using HTTP Basic authentication, as is
# shown below.
#
# Licensed under the terms of the Apache Software License 2.0:
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Questions, comments, feature requests and patches are most welcome.
# Please direct all of these to the Google Code users group:
#  http://groups.google.com/group/google-code-hosting

"""Google Code file uploader script.
"""

__author__ = 'danderson@google.com (David Anderson)'

import httplib
import os.path
import optparse
import getpass
import base64
import sys


def get_svn_config_dir():
  """Return user's Subversion configuration directory."""
  try:
    from win32com.shell.shell import SHGetFolderPath
    import win32com.shell.shellcon
  except ImportError:
    # If we can't import the win32api, just use ~; this is right on unix, and
    # returns not entirely unreasonable results on Windows.
    return os.path.expanduser('~/.subversion')

  # We're on Windows with win32api; use APPDATA.
  return os.path.join(SHGetFolderPath(0, win32com.shell.shellcon.CSIDL_APPDATA,
                                      0, 0).encode('utf-8'),
                      'Subversion')


def get_svn_auth(project_name, config_dir):
  """Return (username, password) for project_name in config_dir."""
  realm = ('<https://%s.googlecode.com:443> Google Code Subversion Repository'
           % project_name)
  authdir = os.path.join(config_dir, 'auth', 'svn.simple')
  for fname in os.listdir(authdir):
      info = {}
      key = None
      for line in open(os.path.join(authdir, fname)):
          line = line.strip()
          if line[0] in 'KV':
              continue
          if line == 'END':
              break
          if line in 'password username svn:realmstring'.split():
              key = line
          else:
              info[key] = line

      if info['svn:realmstring'] == realm:
          return (info['username'], info['password'])
  else:
      return (None, None)

  return result


def upload(file, project_name, user_name, password, summary, labels=None):
  """Upload a file to a Google Code project's file server.

  Args:
    file: The local path to the file.
    project_name: The name of your project on Google Code.
    user_name: Your Google account name.
    password: The googlecode.com password for your account.
              Note that this is NOT your global Google Account password!
    summary: A small description for the file.
    labels: an optional list of label strings with which to tag the file.

  Returns: a tuple:
    http_status: 201 if the upload succeeded, something else if an
                 error occured.
    http_reason: The human-readable string associated with http_status
    file_url: If the upload succeeded, the URL of the file on Google
              Code, None otherwise.
  """
  # The login is the user part of user@gmail.com. If the login provided
  # is in the full user@domain form, strip it down.
  if user_name.endswith('@gmail.com'):
    user_name = user_name[:user_name.index('@gmail.com')]

  form_fields = [('summary', summary)]
  if labels is not None:
    form_fields.extend([('label', l.strip()) for l in labels])

  content_type, body = encode_upload_request(form_fields, file)

  upload_host = '%s.googlecode.com' % project_name
  upload_uri = '/files'
  auth_token = base64.b64encode('%s:%s'% (user_name, password))
  headers = {
    'Authorization': 'Basic %s' % auth_token,
    'User-Agent': 'Googlecode.com uploader v0.9.4',
    'Content-Type': content_type,
    }

  server = httplib.HTTPSConnection(upload_host)
  server.request('POST', upload_uri, body, headers)
  resp = server.getresponse()
  server.close()

  if resp.status == 201:
    location = resp.getheader('Location', None)
  else:
    location = None
  return resp.status, resp.reason, location


def encode_upload_request(fields, file_path):
  """Encode the given fields and file into a multipart form body.

  fields is a sequence of (name, value) pairs. file is the path of
  the file to upload. The file will be uploaded to Google Code with
  the same file name.

  Returns: (content_type, body) ready for httplib.HTTP instance
  """
  BOUNDARY = '----------Googlecode_boundary_reindeer_flotilla'
  CRLF = '\r\n'

  body = []

  # Add the metadata about the upload first
  for key, value in fields:
    body.extend(
      ['--' + BOUNDARY,
       'Content-Disposition: form-data; name="%s"' % key,
       '',
       value,
       ])

  # Now add the file itself
  file_name = os.path.basename(file_path)
  f = open(file_path, 'rb')
  file_content = f.read()
  f.close()

  body.extend(
    ['--' + BOUNDARY,
     'Content-Disposition: form-data; name="filename"; filename="%s"'
     % file_name,
     # The upload server determines the mime-type, no need to set it.
     'Content-Type: application/octet-stream',
     '',
     file_content,
     ])

  # Finalize the form body
  body.extend(['--' + BOUNDARY + '--', ''])

  return 'multipart/form-data; boundary=%s' % BOUNDARY, CRLF.join(body)


def upload_find_auth(file_path, project_name, summary, labels=None,
                     config_dir=None, user_name=None, tries=3):
  """Find credentials and upload a file to a Google Code project's file server.

  file_path, project_name, summary, and labels are passed as-is to upload.

  If config_dir is None, try get_svn_config_dir(); if it is 'none', skip
  trying the Subversion configuration entirely.  If user_name is not None, use
  it for the first attempt; prompt for subsequent attempts.

  Args:
    file_path: The local path to the file.
    project_name: The name of your project on Google Code.
    summary: A small description for the file.
    labels: an optional list of label strings with which to tag the file.
    config_dir: Path to Subversion configuration directory, 'none', or None.
    user_name: Your Google account name.
    tries: How many attempts to make.
  """

  if config_dir != 'none':
    # Try to load username/password from svn config for first try.
    if config_dir is None:
      config_dir = get_svn_config_dir()
    (svn_username, password) = get_svn_auth(project_name, config_dir)
    if user_name is None:
      # If username was not supplied by caller, use svn config.
      user_name = svn_username
  else:
    # Just initialize password for the first try.
    password = None

  while tries > 0:
    if user_name is None:
      # Read username if not specified or loaded from svn config, or on
      # subsequent tries.
      sys.stdout.write('Please enter your googlecode.com username: ')
      sys.stdout.flush()
      user_name = sys.stdin.readline().rstrip()
    if password is None:
      # Read password if not loaded from svn config, or on subsequent tries.
      print 'Please enter your googlecode.com password.'
      print '** Note that this is NOT your Gmail account password! **'
      print 'It is the password you use to access Subversion repositories,'
      print 'and can be found here: http://code.google.com/hosting/settings'
      password = getpass.getpass()

    status, reason, url = upload(file_path, project_name, user_name, password,
                                 summary, labels)
    # Returns 403 Forbidden instead of 401 Unauthorized for bad
    # credentials as of 2007-07-17.
    if status in [httplib.FORBIDDEN, httplib.UNAUTHORIZED]:
      # Rest for another try.
      user_name = password = None
      tries = tries - 1
    else:
      # We're done.
      break

  return status, reason, url


def main():
  try:
      version = sys.argv[1]
  except:
      return 'Usage: %s <version string>'%sys.argv[0]

  summary = dict(
    src='Bruce source distribution',
    linux='Bruce Linux application bundle',
    windows='Bruce Windows application bundle',
    osx='Bruce OS X application bundle',
    examples='Bruce examples bundle',
  )

  for filetype in 'src linux windows osx examples'.split():
    if filetype == 'src':
        filename = 'dist/bruce-%s.tar.gz'%version
    else:
        filename = 'dist/bruce-%s-%s.zip'%(version, filetype)

    status, reason, url = upload_find_auth(filename, 'bruce-tpt',
      summary[filetype], config_dir=os.path.expanduser('~/.subversion'))
    if url:
      print 'Upload success to: %s'%url
      continue
    else:
      return 'Google Code upload error: %s (%s)'%(reason, status)

  return 0
  
if __name__ == '__main__':
  sys.exit(main())

