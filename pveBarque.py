from flask import Flask, request
from flask_restful import Resource, Api, reqparse, abort
from json import dumps
from flask_jsonpify import jsonify
from datetime import datetime
from shutil import copyfile
from glob import glob
import subprocess, os, time

#defaults
__host = "192.168.100.11"
__port = 6969
path = "/root/barque/"
label = "api"

app = Flask(__name__)
api = Api(app)
todos = {}
vmid = 0

parser = reqparse.RequestParser()
parser.add_argument('file','vmid')

class Backup(Resource):
	def post(self, vmid):
		vmdisk = 'vm-{}-disk-1'.format(vmid)
		timestamp = datetime.strftime(datetime.now(),"_%Y-%m-%d_%H-%M")
		#cmd = cmd[:-1] #trim last item from list b/c cmd ends with newline char
		#return {'result': cmd} #return output list as json
		config_file = ""
		config_target = "{}.conf".format(vmid)
		print(config_file)
		for paths, dirs, files in os.walk('/etc/pve/nodes'):
			if config_target in files:
				config_file = os.path.join(paths, config_target)
				print(config_file)
		if len(config_file) == 0:
			return "error, {} is invalid CTID".format(vmid), 400
		config_dest = "".join([path, vmdisk, timestamp, ".conf"])
		copyfile(config_file, config_dest)
		dest = "".join([path, vmdisk, timestamp, ".img"])
		args = ['rbd export --export-format 1 {} {}'.format(vmdisk, dest)]
		cmd = subprocess.check_output(args, shell=True)#.split('\n') #run command then convert output to list, splitting on newline
		return {'Backup file': dest, 'Config file': config_dest}, 201
class Restore(Resource):
	def post(self,vmid):
		#find node hosting container
		config_target = "{}.conf".format(vmid)
		for paths, dirs, files in os.walk('/etc/pve/nodes'):
			if config_target in files:
				config_file = os.path.join(paths, config_target)
				pathlist = os.path.split(config_file)
				print(pathlist)
class ListAllBackups(Resource):
	def get(self):
		result = []
		confs = []
		for paths, dirs, files in os.walk(path):
			for f in files:
				if not f.endswith('.conf'):
					result.append(f)
				elif f.endswith('.conf'):
					confs.append(f)
		return {'all backups': result, 'config files': confs}

class ListBackups(Resource):
	def get(self, vmid):
		files = sorted(os.path.basename(f) for f in glob("".join([path, "vm-{}*.img".format(vmid)])))
		return {'backups': files}
class DeleteBackup(Resource):
	def post(self,vmid):
		if 'file' in request.args:
			print(request.args['file'])
			fullpath = "".join([path, request.args['file']])
			if os.path.isfile(fullpath):
				return {'file exists': fullpath}
			else:
				return {'file does not exist': fullpath}
		else:
			return "resource requires a file argument", 400
		

api.add_resource(ListAllBackups, '/barque/')
api.add_resource(ListBackups, '/barque/<int:vmid>')
api.add_resource(Backup, '/barque/<int:vmid>/backup')
api.add_resource(Restore, '/barque/<int:vmid>/restore')
api.add_resource(DeleteBackup, '/barque/<int:vmid>/delete')

if __name__ == '__main__':
        app.run(host=__host,port=__port, debug=True)