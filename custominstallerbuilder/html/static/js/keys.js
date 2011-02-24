/*****************************************************************
<File Name>
  download.js

<Started>
  January 2011

<Author>
  Alex Hanson

<Purpose>
  Provides interactivity for the download page of the Custom
  Installer Builder.
*****************************************************************/


$(document).ready(function () {
  $('#download_private_keys').click(function () {
    addCheck(this);
    
    $('#public_keys').fadeIn(function () {
      $('#installers').fadeIn();
    });
  });
  
  $('#download_public_keys').click(function () {
    addCheck(this);
  });
});


function addCheck(button) {
  /*****************************************************************
  <Purpose>
    Adds a check mark to the button if one is not already there.
  <Arguments>
    button:
      A button DOM element.
  <Side Effects>
    Puts a lovely unicode check mark in front of the button text.
  <Returns>
    None.
  *****************************************************************/
  
  if ($(button).text().search(new RegExp(/[\u2713]/i)) != -1) {
    return;
  }
  
  $(button).html('&#10003; ' + $(button).html());
}