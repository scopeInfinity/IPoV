import argparse
import logging
from IPoV import IPoV
from config import *

logging.basicConfig()
logger = logging.getLogger("main")
logger.setLevel(log_level)
def get_parser():
	parser = argparse.ArgumentParser()
	parser.add_argument("-s", "--send", nargs='+')
	parser.add_argument("-r", "--receive", action = "store_true")
	return parser

def main():
	connection = IPoV()
	parser = get_parser()
	parser.print_help()
	while True:
		print ">>> ",
		_in = raw_input().split()
		args = parser.parse_args(_in)

		if args.send:
			connection.send(' '.join(args.send))
		else:
			while True:
				data = connection.receive_pull()
				if not data:
					break
				print("'{}' received".format(data))

if __name__ == '__main__':
	main()