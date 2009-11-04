/*
 * setsid.c -- execute a command in a new session
 * Rick Sladkey <jrs@world.std.com>
 * In the public domain.
 *
 * 1999-02-22 Arkadiusz Mi�kiewicz <misiek@misiek.eu.org>
 * - added Native Language Support
 *
 */

/*
 * This should be compiled on mac and freebsd so that we have a setsid command
 * available. It will need to be in the path when run_all_tests.py is run on
 * those systems. If there's some other way to get the setsid command on mac
 * and freebsd, that would be nice, but I'm not sure of the official way of
 * obtaining it for those systems.
 *
 * jsamuel: I've commented out stdio.h and nls.h and related code to get this to
 * compile on mac and freebsd. Note that if you just run this directly from a
 * console like:
 *   ./setsid echo "tests"
 * you'll get an "Operation not permitted" error. The issue, I believe, is that
 * you're trying to call setsid from a process that already is a group leader.
 * If you instead call it from a process that isn't a group leader, it will work.
 * In linux it doesn't complain, and haven't looked into whether that's because
 * the restrictions are different, if it just ignores the setsid, if a console
 * is not a group leader by default, or whatever other explanations there could be.
 */

//#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
//#include "nls.h"

int main(int argc, char *argv[])
{
	//setlocale(LC_ALL, "");
	//bindtextdomain(PACKAGE, LOCALEDIR);
	//textdomain(PACKAGE);
	
	if (argc < 2) {
		//fprintf(stderr, _("usage: %s program [arg ...]\n"),
		//	argv[0]);
		exit(1);
	}
	if (setsid() < 0) {
		perror("setsid");
		exit(1);
	}
	execvp(argv[1], argv + 1);
	perror("execvp");
	exit(1);
}
