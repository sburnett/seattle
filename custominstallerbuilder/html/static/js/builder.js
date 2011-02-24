/*****************************************************************
<File Name>
  builder.js

<Started>
  September 2010

<Author>
  Alex Hanson

<Purpose>
  Provides the interactivity for the builder page of the Custom
  Installer Builder.
*****************************************************************/


/***********************
* CONSTANTS
* Global constants
************************/

var g_max_vessels = 8;


/***********************
* SETUP
* Page initialization function
************************/

$(document).ready(function () {
  // Set the main button handlers.
  $('#reset_button').click(reset_state);
  $('#build_button').click(build_installers);
  
  // Set the iframe handler for adding users.
  $('#user_frame').load(create_user_handler);
  
  // Disable autocomplete for browsers that support the option.
  $('form').attr('autocomplete', 'off');
  
  // Disable text selection in the vessel widget and progress bar.
  $('#vessel_markers').disableTextSelect();
  $('#vessel_widget').disableTextSelect();
  $('#progress').disableTextSelect();
  
  // Set the default AJAX error message.
  jQuery.ajaxSetup({
    'cache': false,
    'error': function (request) {
      error(request.responseText);
    },
  });
  
  // Restore state upon entering the page.
  restore_state();
  
  // Save state upon leaving the page.
  $(window).unload(save_state);
});


/***********************
* FRONTEND
* Functions to maintain frontend state.
************************/

function restore_frontend(build_data) {
  /*****************************************************************
  <Purpose>
    Rebuilds user interface elements from given build data.
  <Arguments>
    build_data:
    The current user/vessel configuration.
  <Side Effects>
    Performs many DOM modifications.
  <Returns>
    None.
  *****************************************************************/
  
  // Clear the current data.
  $('.user').remove();
  $('.vessel').remove();
  
  // Create the user and vessel elements from the provided build data.
  jQuery.each(build_data['users'], function (index, user) { create_user(user); });
  jQuery.each(build_data['vessels'], function (index, vessel) { create_vessel(vessel); });
  
  // Clean up UI elements.
  clear_user_form();
  vessel_markers();
  $('#build_button').removeAttr('disabled');
}

function clear_user_form() {
  /*****************************************************************
  <Purpose>
    Clears any data already entered into the user creation form.
  <Arguments>
    None.
  <Side Effects>
    None.
  <Returns>
    None.
  *****************************************************************/
  
  // Clear the current user name.
  $('#user_form [name="name"]').val('');
  
  // The file input element is wrapped in a span to make it easy to
  // regenerate the input, thus clearing any selected file.
  var file_input_wrapper = $('#user_form [name="public_key"]').parent();
  file_input_wrapper.html(file_input_wrapper.html());
  
  // Automatically set the default user name after selecting a public key.
  $('#user_form [name="public_key"]').change(name_from_file);
}

function name_from_file() {
  /*****************************************************************
  <Purpose>
    Extracts a user name based on the name of the uploaded public key file.
    Sets the user name input box to that value.
  <Arguments>
    None.
  <Side Effects>
    None.
  <Returns>
    None.
  *****************************************************************/
  var file_name = $('#user_form [name="public_key"]').val();
  user_name = file_name.substring(file_name.lastIndexOf('\\') + 1, file_name.lastIndexOf('.'));
  $('[name="name"]', '#user_form').val(user_name);
}

function vessel_markers() {
  /*****************************************************************
  <Purpose>
    Creates and activates the plus-sign vessel markers.
  <Arguments>
    None.
  <Side Effects>
    None.
  <Returns>
    None.
  *****************************************************************/
  
  // Clear current markers to prevent duplicates.
  $('.marker').remove();
  
  // Get the boundaries of the current vessels.
  var current_percentage = 0;
  var boundaries = [];
  
  $('.vessel').not(':last').each(function (index, vessel) {
    current_percentage += $(vessel).data('percentage');
    boundaries.push(current_percentage);
  });
  
  // If g_max_vessels is equal to n, create n-1 markers.
  for (var i = 1; i < g_max_vessels; i++) {
    var offset = (80 / g_max_vessels) * i;
    
    var marker = $('#vessel_markers .sample').clone();
    marker.removeClass('sample').addClass('marker');
    marker.css('width', (80 / g_max_vessels) + '%');
    marker.data('offset', offset);
    
    $('span', marker).click(insert_vessel);
    
    if (jQuery.inArray(offset, boundaries) > -1) {
      $('span', marker).hide();
    }
    
    marker.appendTo('#vessel_markers');
  }
}



/***********************
* BUILD CONFIGURATION
* Functions to manipulate build configuration data.
************************/

function create_user_handler(event) {
  /*****************************************************************
  <Purpose>
    Serves as a handler for new user submissions. Orchestrates the hackish
    invisible iframe AJAX solution, which is necessary for file uploads.
  <Arguments>
    event:
    A javascript event object.
  <Side Effects>
    None.
  <Returns>
    None.
  *****************************************************************/
  
  // Grab the results from the iframe. This only works because the data is not HTML formatted.
  results = JSON.parse($(event.target).contents().text());
  
  if ('error' in results) {
    error(results['error']);
  } else if ('user' in results) {    
    // Construct an array of the current user names.
    var user_names = jQuery.map($('#user_list .user'), function (user_element) { return $(user_element).data('name'); });
    var user = results['user'];
    
    // Add the user if the name is not already taken.
    if (jQuery.inArray(user['name'], user_names) == -1) {
      clear_user_form();
      create_user(user);
    } else {
      error('Duplicate user names are not allowed.');
    }
  }
}

function create_user(user) {
  /*****************************************************************
  <Purpose>
    After basic checks by the handler above, this function actually creates
    the new user.
  <Arguments>
    user:
    An associative array of user data.
  <Side Effects>
    None.
  <Returns>
    None.
  *****************************************************************/
  
  // Create hidden element for the new user.
  var user_element = $('#user_list .sample').clone()
  user_element.removeClass('sample').addClass('user').hide();
  
  if (!user['public_key']) {
    user_element.addClass('new');
  }
  
  // Set the metadata.
  user_element.data('name', user['name']);
  user_element.data('public_key', user['public_key']);
  
  // Set the user name to be displayed.
  $('.name', user_element).html(user['name']);
  
  // Set the delete handler.
  $('.remove', user_element).click(function () { remove_user(user['name']); });
  
  // Make the user draggable.
  user_element.draggable({'opacity': 0.7, 'helper': 'clone'});
  
  // Prevent a text selection cursor during dragging.
  user_element.onselectstart = function () { return false; };
  
  // Append the user to the list and fade the element in.
  user_element.appendTo('#user_list').fadeIn('100');
}

function remove_user(name) {
  /*****************************************************************
  <Purpose>
    Removes all traces of the user with the given name.
  <Arguments>
    name:
    The user name to be removed.
  <Side Effects>
    None.
  <Returns>
    None.
  *****************************************************************/
  
  // Find all user elements with the given name.
  elements = jQuery.grep($('.user'), function (element) { return $(element).data('name') == name; });
  
  // Fade out the user elements and remove them from the DOM.
  $(elements).each(function (index, element) {
    $(element).fadeOut(100, function() { $(this).remove(); });
  });
}

function insert_vessel(event) {
  /*****************************************************************
  <Purpose>
    An event handler for vessels that shrinks the associated vessel, allowing
    the creation of a new one.
  <Arguments>
    event:
    A javascript event.
  <Side Effects>
    None.
  <Returns>
    None.
  *****************************************************************/
  
  // Select and hide the clicked marker.
  var marker = $(event.target).parents('.marker');
  $('span', marker).hide();
  
  // Select the vessel directly to the left of the marker. 
  var current_vessel = find_vessel(marker.data('offset'));
  
  // Calculate the new (smaller) percentage for the original vessel.
  var old_percentage = current_vessel.data('percentage');
  var new_percentage = marker.data('offset') - current_vessel.data('offset');
  
  // Assign the new percentage to the original vessel.
  resize_vessel(current_vessel, new_percentage);
  
  // Create a new vessel to fill in the gap.
  var new_vessel = create_vessel({
    'percentage': old_percentage - new_percentage,
    'owner': null,
    'users': [],
  }, false);
  
  // Associate this marker with the new vessel.
  new_vessel.data('marker', marker);
  
  // Insert the new vessel after the original one.
  new_vessel.insertAfter(current_vessel);
}

function find_vessel(search_percentage) {
  /*****************************************************************
  <Purpose>
    Given a percentage value, returns the vessel which occupies that region
    on the vessel widget.
  <Arguments>
    search_percentage:
    The position to look for the vessel, with the left edge of the widget
    equalling zero percent.
  <Side Effects>
    None.
  <Returns>
    If found, returns a jQuery object of the found vessel.
    Otherwise, returns false.
  *****************************************************************/
  var current_percentage = 0;
  var match;
  
  // Iterate through the vessels left to right until we find the vessel.
  $('.vessel').each(function (index, vessel) {
    var offset = current_percentage;
    current_percentage += $(vessel).data('percentage');
    
    // If a match is found, store the result and break the loop.
    if (current_percentage >= search_percentage) {
      match = $(vessel);
      match.data('offset', offset);
      return false;
    }
  });
  
  return match;
}

function create_vessel(vessel, append) {
  /*****************************************************************
  <Purpose>
    Creates a new vessel.
  <Arguments>
    vessel:
    An associative array of data describing the new vessel.
    append:
    If false, the newly created vessel will not be automatically added to
    the widget. Otherwise, it will be.
  <Side Effects>
    None.
  <Returns>
    The created vessel element.
  *****************************************************************/
  
  if (append === undefined) {
    append = true;
  }
  
  // Create hidden element for the new vessel.
  var vessel_element = $('#vessels .sample').clone();
  vessel_element.removeClass('sample').addClass('vessel');
  
  // Set the metadata.
  vessel_element.data('percentage', vessel['percentage']);

  vessel_element.css('width', vessel['percentage'] + '%');  
  vessel_element.css('max-width', vessel['percentage'] + '%');
  
  if (vessel['owner']) {
    set_vessel_owner(vessel_element, vessel['owner']);
  }
  
  jQuery.each(vessel['users'], function (index, user_name) {
    add_vessel_user(vessel_element, user_name);
  });
  
  // Make the owner area droppable.
  $('.owner', vessel_element).droppable({
		'accept': '.user',
		'activeClass': 'active',
		'hoverClass': 'hover',
		'drop': function(event, ui) {
		  var vessel = $(event.target).parents('.vessel');
		  var user = ui.draggable.clone(true);
		  
		  set_vessel_owner(vessel, user.data('name'));
		},
	});
	
	// Make the users list droppable.
	$('.users', vessel_element).droppable({
		'accept': '.user',
		'activeClass': 'active',
		'hoverClass': 'hover',
		'drop': function(event, ui) {
		  var vessel = $(event.target).parents('.vessel');
		  var user = ui.draggable.clone(true);
		  
		  add_vessel_user(vessel, user.data('name'));
		},
	});
	
	$('.remove', vessel_element).click(remove_vessel);
	
	// Give the vessel a remove button, unless it is the first.
	// A vessel is assumed to be first if none others are visible.
 	if ($('.vessel').size() != 0) {
 	  vessel_element.removeClass('hideRemove');
 	}
  
  if (append) {
     vessel_element.insertBefore('#vessels .reserved');
  }
  
  return vessel_element;
}

function remove_vessel(event) {
  /*****************************************************************
  <Purpose>
    An event handler that removes the associated vessel.
  <Arguments>
    event:
    A javascript event object.
  <Side Effects>
    None.
  <Returns>
    None.
  *****************************************************************/
  
  // Select the vessel to be removed, and its neighbor to be resized.
  var vessel = $(event.target).parents('.vessel');
  var neighbor = vessel.prev();
  
  // Calculate the new percentage of the neighboring vessel.
  var percentage = vessel.data('percentage') + neighbor.data('percentage');
  
  // Remove the selected vessel and resize its neighbor.
  vessel.remove();
  resize_vessel(neighbor, percentage);
  
  // Regenerate vessel markers.
  vessel_markers();
}

function resize_vessel(vessel, percentage) {
  /*****************************************************************
  <Purpose>
    Resizes the given vessel to fit the given percentage.
  <Arguments>
    vessel:
    The vessel to resize.
    percentage:
    The new size of the vessel.
  <Side Effects>
    None.
  <Returns>
    None.
  *****************************************************************/
  vessel.data('percentage', percentage);
  vessel.css('width', percentage + '%');
  vessel.css('max-width', percentage + '%');
}

function set_vessel_owner(vessel, user_name) {
  /*****************************************************************
  <Purpose>
    Sets the owner of a particular vessel.
  <Arguments>
    vessel:
    The vessel to be modified.
    user_name:
    The owner to be assigned.
  <Side Effects>
    None.
  <Returns>
    None.
  *****************************************************************/
  var user_element = $('#user_list .sample').clone();
  user_element.removeClass('sample').addClass('user');

  user_element.data('name', user_name);
  
  $('.name', user_element).html(user_name);
  $('.owner', vessel).html(user_element);
  
  $('.remove', user_element).click(function (event) {
    $(event.target).parents('.user').remove(); 
  });
}

function add_vessel_user(vessel, user_name) {
  /*****************************************************************
  <Purpose>
    Adds a user to a particular vessel.
  <Arguments>
    vessel:
    The vessel to be modified.
    user_name:
    The user to be added.
  <Side Effects>
    None.
  <Returns>
    None.
  *****************************************************************/
  var elements = jQuery.grep($('.users .user', vessel), function (element) { return $(element).data('name') == user_name; });

  if (elements.length > 0) {
    return;
  }
  
  var user = $('#user_list .sample').clone();
  user.removeClass('sample').removeClass('round_shadow').addClass('user');
  
  user.data('name', user_name);
  
  $('.name', user).html(user_name);
  $('.users', vessel).append(user);
  
  $('.remove', user).click(function (event) {
    $(event.target).parents('.user').remove(); 
  });
}


/***********************
* STATE MANIPULATION
* Functions that either save, restore, or clear overall build state.
************************/

function save_state() {
  /*****************************************************************
  <Purpose>
    Saves the current build data to the server for later restoration or
    installer building.
  <Arguments>
    None.
  <Side Effects>
    None.
  <Returns>
    None.
  *****************************************************************/
  
  var build_data = {};
  
  build_data['users'] = jQuery.map($('#user_list .user'), function (user_element) {
    return {
      'name': $(user_element).data('name'),
      'public_key': $(user_element).data('public_key'),
    };
  });
  
  build_data['vessels'] = jQuery.map($('#vessels .vessel'), function (vessel_element) {
    return {
      'percentage': $(vessel_element).data('percentage'),
      'owner': $(vessel_element).find('.owner .user').data('name'),
      'users': jQuery.map($(vessel_element).find('.users .user'), function (user_element) {
        return $(user_element).data('name');
      }),
    };
  });
  
  var build_string = JSON.stringify(build_data);
  
  $.ajax({
    'url': 'ajax/save/',
    'type': 'POST',
    'data': {'build_string': build_string},
    'async': false,
  });
}

function restore_state(reset) {
  /*****************************************************************
  <Purpose>
    Retrieves the most recently stored build data from the server and
    restores it back to the client interface. Optionally can be used to reset
    all build data.
  <Arguments>
    reset:
    If true, the restored data will be the default (blank) configuration.
  <Side Effects>
    None.
  <Returns>
    None.
  *****************************************************************/
  if (reset === undefined) {
    reset = false;
  }
  
  if (reset) {
    var url = 'ajax/reset/';
  } else {
    var url = 'ajax/restore/'
  }
  
  $.ajax({
    'url': url,
    'type': 'GET',
    'success': function (build_string) {
      var build_data = JSON.parse(build_string);
      restore_frontend(build_data);
    },
  });
}

function reset_state() {
  /*****************************************************************
  <Purpose>
    A shortcut for resetting the build state.
  <Arguments>
    None.
  <Side Effects>
    None.
  <Returns>
    None.
  *****************************************************************/
  restore_state(true);
  hide_status();
}

function build_installers() {  
  /*****************************************************************
  <Purpose>
    Saves the current build data to the server and attempts to build the
    installers, reporting any error that may arise.
  <Arguments>
    None.
  <Side Effects>
    None.
  <Returns>
    None.
  *****************************************************************/
  
  // Disable the build button while a build is in progress.
  $('#build_button').attr('disabled', 'disabled');
  $('#build_loading').addClass('active');
  
  hide_status();
  
  // Syncronize the build data back to the server.
  save_state();
  
  // Initiate the build, redirecing upon success or displaying a message
  // upon error.
  $.ajax({
    'url': 'ajax/build/',
    'type': 'GET',
    'success': function (download_url) {
      $(window).unbind('unload');
      window.location = download_url;
    },
    'error': function (request) {
      error(request.responseText);
      $('#build_button').removeAttr('disabled');
      $('#build_loading').removeClass('active');
    },
  });
}
