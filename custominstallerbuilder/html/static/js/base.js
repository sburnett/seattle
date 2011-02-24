/*****************************************************************
<File Name>
  base.js

<Started>
  January 2011

<Author>
  Alex Hanson

<Purpose>
  Provides interactivity common across multiple pages of the
  Custom Installer Builder.
*****************************************************************/


function status(message, error) {
  /*****************************************************************
  <Purpose>
    Sets the given message as the status in the blue status bar on top of
    the page. Optionally, can deliver a red error message instead.
  <Arguments>
    message:
    The message to be set.
    error:
    If true, set the status area red to indicate an error.
  <Side Effects>
    None.
  <Returns>
    None.
  *****************************************************************/
  
  if (error === undefined) {
    error = false;
  }
  
  var status = $('#status');
  
  status.hide();
  
  if (error) {
    status.addClass('error');
  } else {
    status.removeClass('error');
  }
  
  $('.content', status).html(message);
  
  status.fadeIn('fast');
}

function error(message) {
  /*****************************************************************
  <Purpose>
    Sets an error message in the status bar.
  <Arguments>
    message:
    The message to be set.
  <Side Effects>
    None.
  <Returns>
    None.
  *****************************************************************/
  
  status(message, true);
}

function hide_status() {
  /*****************************************************************
  <Purpose>
    Hides the status bar.
  <Arguments>
    None.
  <Side Effects>
    None.
  <Returns>
    None.
  *****************************************************************/
  
  $('#status').fadeOut('fast');  
}
