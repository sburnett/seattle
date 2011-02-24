"""
<Program Name>
  views.py

<Started>
  September 2010

<Author>
  Alex Hanson

<Purpose>
  Provides an XML-RPC dispatcher for use by a request handler, e.g. within a
  Django view. The dispatcher is essentially nothing more than a class which
  holds the functions to be exposed over XML-RPC.
"""

import os

from django.conf import settings

import custominstallerbuilder.common.validations as validations
from custominstallerbuilder.common.build_manager import BuildManager





class PublicFunctions:
  """
  <Purpose>
    Wraps all public XML-RPC functions into a single class, which can be
    passed to a request handler
    
  <Side Effects>
    The called XML-RPC functions may have side effects.
    
  <Example Use>
    # Create an XML-RPC request handler
    handler = CGIXMLRPCRequestHandler(allow_none=False, encoding=None)
    
    # Let PublicFunctions accept the procedure calls.
    handler.register_instance(PublicFunctions())
    
    # Interpret an XML-RPC request from marshalled XML.
    response_data = handler._marshaled_dispatch(marshalled_xml)
  """
  
  
  
  
      
  def api_version(self):
    """
    <Purpose>
      Allows XML-RPC clients to query the current version of the installer
      builder API.

    <Arguments>
      None.

    <Exceptions>
      None.

    <Side Effects>
      None.

    <Returns>
      A string representing the current version of the Custom Installer Builder
      API.
    """
    
    return settings.API_VERSION





  def build_installers(self, vessel_list, user_data=None):
    """
    <Purpose>
      Allows XML-RPC clients to build installers.

    <Arguments>
      vessels:
        A list of vessels, each represented by a dictonary. The dictionary
        should contain 'percentage', 'owner', and (optionally) 'users'
        entries.
        
      platforms:
        A list of platforms for which to build the installers, such as
        'linux', 'mac', or 'windows'.
        
      user_data:
        An optional dictionary with user names as keys, and sub-dictionaries
        as values. The sub-dictionaries may contain a 'public_key' entry.

    <Exceptions>
      ValidationError if malformed data was passed.

    <Side Effects>
      Creates the desired installers and writes them to disk.

    <Returns>
      A dictionary which contains the build ID, URLs pointing to the
      newly built installers, and a dictionary of user cryptographic keys.
    """
    
    manager = BuildManager(vessel_list, user_data)
    return manager.prepare()





  def get_urls(self, build_id):
    """
    <Purpose>
      Allows XML-RPC clients request the URLs for builds other than their own.

    <Arguments>
      build_id:
        The build ID of a previously generated custom installer.

    <Exceptions>
      ValidationError if improper build_id is passed.

    <Side Effects>
      None.

    <Returns>
      A dictionary which contains URLs pointing to the installers, and a
      dictionary of user cryptographic keys.
    """

    validations.validate_build_id(build_id)

    manager = BuildManager(build_id=build_id)

    if not os.path.isdir(manager.get_build_directory()):
      raise validations.ValidationError('Given build ID does not exist.')

    return manager.get_urls()
