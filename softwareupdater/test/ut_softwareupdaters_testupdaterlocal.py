"""
File: ut_softwareupdater_localtest.py
"""

#pragma out [ PASS ]

import os
import sys
import imp
import glob
import time
import shutil
import logging
import urllib2
import StringIO
import tempfile
import subprocess
from SocketServer import TCPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler

import runonce
from harshexit import portablekill

class Server(TCPServer):
	allow_reuse_address = True

def _repo_server(server_root, port, lockfile_path):
	try:
		sys.stdout = StringIO.StringIO()
		sys.stderr = StringIO.StringIO()
		os.chdir(server_root)
		srvr = Server(("", int(port)), SimpleHTTPRequestHandler)
		while os.path.exists(lockfile_path):
			srvr.handle_request()
	except Exception, e:
		print(e)

class Scenario:

	def __init__(self, project_root, port=12345):

		self.port = port
		self.address = 'http://localhost:%s' % port
		self.server = None

		self.lockfile_path = None

		self.project_root = project_root
		self.scenario_root = tempfile.mkdtemp()

		self._prepare_scenario_root()

		self.client_root = os.path.join(self.scenario_root, "client")

		self.client_repo_path = os.path.join(self.client_root, "repo")

		self.client_current_metadata = os.path.join(self.client_repo_path, "cur")

		self.client_previous_metadata = os.path.join(self.client_repo_path, "prev")

		self.server_root = os.path.join(self.scenario_root, "server")
		os.mkdir(self.server_root)

		self.server_metadata_path = os.path.join(self.server_root, "meta")
		os.mkdir(self.server_metadata_path)

		self.server_targets_path = os.path.join(self.server_root, "targets")

		self.keystore_path = os.path.join(self.scenario_root, "keystore")

	def _prepare_scenario_root(self):
		#preparetest_args = [	"python",
		#			"preparetest.py",
		#			"-t",
		#			self.scenario_root]
		#subprocess.call(preparetest_args)
		sys.path.append(self.scenario_root)
		import softwareupdater
		self.updater = softwareupdater

	def run_test(self):
		self.pre_server_action()
		self.make_server()
		self.post_server_action()
		self.make_client()
		self.post_client_action()
		tmp_dir = tempfile.mkdtemp()
		updates = self.updater.do_rsync(	self.address,
							self.client_root,
							tmp_dir,
							self.client_root)
		self.stop_repo_server()
		return self.evaluate_updates(updates)

	def run_live_test(self):
		self.pre_server_action()
		self.make_server()
		self.post_server_action()
		self.make_client()
		self.post_client_action()	
		args = ["python", "softwareupdater.py", "debug"]
		out = subprocess.call(args, cwd=self.client_root)
		self.stop_repo_server()
		if not out:
			return True
		else:
			return False

	def make_client(self):
		shutil.copytree(self.project_root, self.client_root)
		os.makedirs(self.client_current_metadata)
		os.makedirs(self.client_previous_metadata)
		for f in glob.iglob(os.path.join(self.server_metadata_path, "*")):
			shutil.copy(f, self.client_current_metadata)
		for f in glob.iglob(os.path.join(self.server_metadata_path, "*")):
			shutil.copy(f, self.client_previous_metadata)

	def make_server(self):
		args = ["python",
			"quickstart.py",
			"-k",
			self.keystore_path,
			"-t",
			"1",
			"-l",
			self.server_root,
			"-r",
			self.project_root,
			"--test",
			"-e",
			"12/12/2012"]
		subprocess.call(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		self.start_repo_server()

	def start_repo_server(self):
		self.lockfile_path = tempfile.mktemp()
		open(self.lockfile_path, "w").close()
		srvr_args = ['python', 'ut_softwareupdaters_testupdaterlocal.py', self.server_root, str(self.port), self.lockfile_path]
		self.server = subprocess.Popen(srvr_args)
		for i in range(5):
			try:
				urllib2.urlopen(self.address)
			except Exception, e: 
				time.sleep(1)
			else:
				break
		else:
			raise Exception("Server didn't start!")

	def stop_repo_server(self):
		if self.server is None:
			return
		if self.address is None:
			raise Exception("Address set but not the server!")
		if self.lockfile_path:
			try: os.remove(self.lockfile_path)
			except Exception: pass

		portablekill(self.server.pid)

		for i in range(5):
			try: urllib2.urlopen(self.address)
			except Exception: break
			time.sleep(1)
		else:
			raise Exception("Server didn't stop!")

	def pre_server_action(self):
		pass

	def post_server_action(self):
		pass

	def post_client_action(self):
		pass

	def evaluate_updates(self, updates):
		pass

	def cleanup(self):
		self.stop_repo_server()
		try: os.remove(self.lockfile_path)
		except Exception: pass
		try: shutil.rmtree(self.scenario_root)
		except Exception: pass


class NoUpdateTest(Scenario):

	def evaluate_updates(self, updates):
		if updates: return False
		return True


class BadSignatureTest(Scenario):

	def start_repo_server(*args, **kwargs):
		pass

	def pre_server_action(self):
		# we actually build a separate server to connect to
		self.noup = NoUpdateTest(self.project_root)

	def cleanup(self):
		self.stop_repo_server()
		self.noup.stop_repo_server()
		self.noup.cleanup()
		try: shutil.rmtree(self.scenario_root)
		except OSError: pass

	def evaluate_updates(self, updates):
		print(updates)
		if updates: return False
		return True


class UpdateTest(Scenario):

	def post_client_action(self):
		# stop the existing server
		self.stop_repo_server()
		self.address = "http://localhost:%d" % self.port
		cfg_path = os.path.join(self.server_root, 'root.cfg')
		shutil.copy(cfg_path, self.project_root)
		shutil.rmtree(self.server_targets_path)
		shutil.copytree(self.client_root, self.server_targets_path)
		args = ["python",
			"quickstart.py",
			"-u",
			"-k",
			self.keystore_path,
			"-l",
			self.server_root,
			"--test",
			"-r",
			self.server_targets_path,
			"-c",
			cfg_path]
		subprocess.call(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		self.start_repo_server()
		os.remove(cfg_path)

	def evaluate_updates(self, updates):
		correct_updates = [	'repo/cur/targets.txt', 
					'repo/cur/timestamp.txt',
					'repo/cur/release.txt']
		if set(updates) < set(correct_updates):
			return False
		return True


class RestartTest(Scenario):

	added_string = '# this is a comment'

	def run_live_test(self):
		self.pre_server_action()
		self.make_server()
		self.post_server_action()
		self.make_client()
		self.post_client_action()	
		args = ["python", "softwareupdater.py", "debug"]
		out = subprocess.call(args, cwd=self.client_root)
		return out == 10

	def modify_softwareupdater(self, dirpath):
		location = os.path.join(dirpath, 'softwareupdater.py')
		f = open(location, 'a')
		f.write(self.added_string)
		f.close()

	def post_client_action(self):
		# stop the existing server
		self.stop_repo_server()
		self.address = "http://localhost:%d" % self.port
		cfg_path = os.path.join(self.server_root, 'root.cfg')
		shutil.copy(cfg_path, self.project_root)
		shutil.rmtree(self.server_targets_path)
		shutil.copytree(self.client_root, self.server_targets_path)
		self.modify_softwareupdater(self.server_targets_path)
		args = ["python",
			"quickstart.py",
			"-u",
			"-k",
			self.keystore_path,
			"-l",
			self.server_root,
			"--test",
			"-r",
			self.server_targets_path,
			"-c",
			cfg_path]
		subprocess.call(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		self.start_repo_server()
		os.remove(cfg_path)

	def evaluate_updates(self, updates):
		if 'softwareupdater.py' not in updates:
			print(updates)
			return False
		return True

if __name__ == "__main__":

	import sys
	if len(sys.argv) == 4:
		server_root = sys.argv[1]
		port = int(sys.argv[2])
		lockfile_path = sys.argv[3]
		_repo_server(server_root, port, lockfile_path)
		sys.exit(0)

	results = []

	working_dir = os.getcwd()

	noup_live = NoUpdateTest(working_dir)
	results.append(noup_live.run_live_test())
	noup_live.cleanup()
	
	noup = NoUpdateTest(working_dir)
	results.append(noup.run_test())
	noup.cleanup()
	
	bad_sig = BadSignatureTest(working_dir)
	try:
		err = False
		bad_sig.run_test()
	except Exception, e:
		err = True
	results.append(err)
	bad_sig.cleanup()

	fourup = UpdateTest(working_dir)
	results.append(fourup.run_test())
	fourup.cleanup()

	fourup_live = UpdateTest(working_dir)
	results.append(fourup_live.run_live_test())
	fourup_live.cleanup()

	restart = RestartTest(working_dir)
	results.append(restart.run_test())
	restart.cleanup()

	restart_live = RestartTest(working_dir)
	results.append(restart_live.run_live_test())
	restart_live.cleanup()

	# get any remaining softwareupdaters and kill them
	while 1:
		pid = runonce.getprocesslock('softwareupdater.old')
		if pid == True:
			runonce.releaseprocesslock('softwareupdater.old')
			break
		elif pid == False:
			print '[ FAIL ]',
			sys.exit(1)
		else:
			portablekill(pid)

	while 1:
		pid = runonce.getprocesslock('softwareupdater.new')
		if pid == True:
			runonce.releaseprocesslock('softwareupdater.new')
			break
		elif pid == False:
			print '[ FAIL ]',
			sys.exit(1)
		else:
			portablekill(pid)

	if all(results) and (len(results) == 7):
		print "[ PASS ]",
	else:
		print results
		print "[ FAIL ]",
