][oLevel] ) { openLists[oBsID][oLevel] = null; }
	    else { oThisOb.style.display = 'block'; openLists[oBsID][oLevel] = oThisOb; }
} else { oThisOb.style.display = ( oThisOb.style.display == 'block' ) ? 'none' : 'block'; }
}
function stateToFromStr(oID,oFStr) {
    if( !document.getElementsByTagName || !document.childNodes || !document.createElement ) { return ''; }
    var baseElement = document.getElementById( oID ); if( !baseElement ) { return ''; }
    if( !oFStr && typeof(oFStr) != 'undefined' ) { return ''; } if( oFStr ) { oFStr = oFStr.split(':'); }
    for( var oStr = '', l = baseElement.getElementsByTagName(baseElement.tagName), x = 0; l[x]; x++ ) {
	if( oFStr && MWJisInTheArray( l[x].MWJuniqueID, oFStr ) && l[x].style.display == 'none' ) { l[x].parentNode.getElementsByTagName('a')[0].onclick(); }
	else if( l[x].style.display != 'none' ) { oStr += (oStr?':':'') + l[x].MWJuniqueID; }
    }
    return oStr;
}
function MWJisInTheArray(oNeed,oHay) { for( var i = 0; i < oHay.length; i++ ) { if( oNeed == oHay[i] ) { return true; } } return false; }
function selfLink(oRootElement,oClass,oExpand,oLink) {
    var tmpLink;
    if(!document.getElementsByTagName||!document.childNodes) { return; }
    oRootElement = document.getElementById(oRootElement);
    if( oLink ) {
	tmpLink = document.createElement('a');
	tmpLink.setAttribute('href',oLink);
    }
    for( var x = 0, y = oRootElement.getElementsByTagName('a'); y[x]; x++ ) {
	if( y[x].getAttribute('href') && !y[x].href.match(/#$/) && getRealAddress(y[x]) == getRealAddress(oLink?tmpLink:location) ) {
	    y[x].className = (y[x].className?(y[x].className+' '):'') + oClass;
	    if( oExpand ) {
		oExpand = false;
		for( var oEl = y[x].parentNode, ulStr = ''; oEl != oRootElement && oEl != document.body; oEl = oEl.parentNode ) {
		    if( oEl.tagName && oEl.tagName == oRootElement.tagName ) { ulStr = oEl.MWJuniqueID + (ulStr?(':'+ulStr):''); } }
		stateToFromStr(oRootElement.id,ulStr);
	    } } } }
function getRealAddress(oOb) { return oOb.protocol + ( ( oOb.protocol.indexOf( ':' ) + 1 ) ? '' : ':' ) + oOb.hostname + ( ( typeof(oOb.pathname) == typeof(' ') && oOb.pathname.indexOf('/') != 0 ) ? '/' : '' ) + oOb.pathname + oOb.search; }
function expandCollapseAll(oElID,oState) {
    if(!document.getElementsByTagName||!document.childNodes) { return; }
    var oEl = document.getElementById(oElID);
    var oT = oEl.tagName;
    var oULs = oEl.getElementsByTagName(oT);
    for( var i = 0, oLnk; i < oULs.length; i++ ) {
	if( typeof(oULs[i].MWJuniqueID) != 'undefined' ) {
	    oLnk = oULs[i].parentNode.getElementsByTagName( 'a' )[0];
	    if( oLnk && ( ( oState && oULs[i].style.display == 'none' ) || ( !oState && oULs[i].style.display != 'none' ) ) ) {
		oLnk.onclick();
	    } } } }