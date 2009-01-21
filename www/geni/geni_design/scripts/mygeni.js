$(document).ready(function() {
    
});

/*
    Create a block with given width and background color,
    and append it to the given bar element.
*/

function create_block (bar, width, color) {
    var block = $(document.createElement("td"));
    block.css({
        'width': width,
        'background-color': color
    });
    bar.append(block);
}