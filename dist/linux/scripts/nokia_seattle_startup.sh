#! /bin/sh

# Seattle start-up initialization script for Nokia tablets
# Author: Derek Cheng
# Date: 1/3/2010
# This script is to be run manually as root after install.sh for Nokia tablets 
# in order to start Seattle on startup. This script writes a short shell script
# to /etc/init.d (by default) and creates a soft link to it to /etc/rc2.d (by
# default). The written script, which will be run on startup, will in turn run 
# the target script (i.e., start_seattle.sh).
# If the -r flag is passed as the first argument to this script, then the files
# are removed instead.
# This script is also to be run manually with the -r flag as root after 
# uninstalling to remove the startup script/link.

# The username of the user who will start Seattle. ("user" by default)
USERNAME="user"

# The name of the script to be put in the init.d directory.
STARTSCRIPTNAME="start_sea.sh"
# The directory in which the startup script is put. (/etc/init.d)
STARTSCRIPTDIR="/etc/init.d"
# The path of the startup script.
STARTSCRIPTPATH=${STARTSCRIPTDIR}/${STARTSCRIPTNAME}

# The name of the symlink to be put in the rc directory.
LINKNAME="S99startseattle"
# The directory of rc. On Nokia N800, the default level is 2. (/etc/rc2.d)
LINKDIR="/etc/rc2.d"
# The path of the link.
LINKPATH=${LINKDIR}/${LINKNAME}

# The name of the script to be run by the startup script. (start_seattle.sh)
TARGETSCRIPTNAME="start_seattle.sh"
# The directory of start_seattle.sh. (the current directory)
TARGETSCRIPTDIR="`pwd`"
# The path of the target script.
TARGETSCRIPTPATH=${TARGETSCRIPTDIR}/${TARGETSCRIPTNAME}

if [ $# -gt 0 ]
then
    if [ $1 = "-r" ]
	then
	# -r means to remove instead of create.
	rm -f ${LINKPATH} ${STARTSCRIPTPATH}
	if [ $? -ne 0 ]
	then
	    echo "Cannot remove startup script/link: are you root?"
	    return 2
	else
	    echo "Seattle startup removal successful."
	    return 0
	fi
    else
	# Bad arguments
	echo "usage: $0 [-r]"
	return 128
    fi

else    
# No flags - normal installation.

# Test if the file already exists.
    if [ -e ${STARTSCRIPTPATH} ]
    then
	echo "${STARTSCRIPTPATH} already exists: is Seattle already installed?"
	return 1
    fi 
    
# Writes the short script that will cause the startup script to run the 
# target script as "user" (The username of the user on Nokia N800).
    echo "#! /bin/sh" >> ${STARTSCRIPTPATH}
    echo "su - ${USERNAME} -c ${TARGETSCRIPTPATH}" >> ${STARTSCRIPTPATH}
    if [ $? -ne 0 ]
    then
	echo "Cannot create/write to ${STARTSCRIPTPATH}: are you root?"
	rm -f ${STARTSCRIPTPATH}
	return 2
    fi
    
    chmod +x ${STARTSCRIPTPATH}
    if [ $? -ne 0 ]
    then
	echo "Cannot change permission of ${STARTSCRIPTNAME}: are you root?"
	rm -f ${STARTSCRIPTPATH}
	return 2
    fi
    
# Now make a symlink in the rc directory.
    ln -s ${STARTSCRIPTPATH} ${LINKPATH}
    if [ $? -ne 0 ]
    then
	echo "Cannot create link ${LINKPATH}, or it already exists - is \
Seattle already installed?"
	rm -f ${STARTSCRIPTPATH}
	return 4
    fi
    
    echo "Created ${STARTSCRIPTNAME} at ${STARTSCRIPTDIR}"
    echo "Created symlink ${LINKNAME} at ${LINKDIR}"
    echo "The Seattle start script (${TARGETSCRIPTPATH}) will run on startup."
    return 0

fi
