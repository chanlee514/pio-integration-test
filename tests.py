import os
import sys
import unittest
import argparse
import xmlrunner
import logging
import pio_tests.globals as globals
from utils import srun_bg
from pio_tests.integration import TestContext
from pio_tests.scenarios.quickstart_test import QuickStartTest
from pio_tests.scenarios.basic_app_usecases import BasicAppUsecases

parser = argparse.ArgumentParser(description='Integration tests for PredictionIO')
parser.add_argument('--eventserver-ip', default='0.0.0.0')
parser.add_argument('--eventserver-port', type=int, default=7070)
parser.add_argument('--no-shell-stdout', action='store_true',
        help='Suppress STDOUT output from shell executed commands')
parser.add_argument('--no-shell-stderr', action='store_true',
        help='Suppress STDERR output from shell executed commands')
parser.add_argument('--logging', action='store', choices=['INFO', 'DEBUG', 'NO_LOGGING'],
        default='NO_LOGGING', help='Choose the logging level')
parser.add_argument('--tests', nargs='*', type=str,
        default=None, help='Names of the tests to execute. By default all tests will be checked')

TESTS_DIRECTORY = os.path.abspath(os.path.dirname(__file__))
ENGINE_DIRECTORY = os.path.join(TESTS_DIRECTORY, "engines")
DATA_DIRECTORY = os.path.join(TESTS_DIRECTORY, "data")

LOGGING_FORMAT = '[%(levelname)s] %(module)s %(asctime)-15s: %(message)s'
logging.basicConfig(format=LOGGING_FORMAT)

def get_tests(test_context):
    # ========= ADD TESTS HERE!!! ================================
    return {'QuickStart': QuickStartTest(test_context),
            'BasicAppUsecases': BasicAppUsecases(test_context)}

if __name__ == "__main__":
    args = vars(parser.parse_args())

    if args.get('no_shell_stdout'):
        globals.SUPPRESS_STDOUT = True
    if args.get('no_shell_stderr'):
        globals.SUPPRESS_STDERR = True

    # setting up logging
    log_opt = args['logging']
    logger = logging.getLogger(globals.LOGGER_NAME)
    if log_opt == 'INFO':
        logger.level = logging.INFO
    elif log_opt == 'DEBUG':
        logger.level = logging.DEBUG

    test_context = TestContext(
            ENGINE_DIRECTORY, DATA_DIRECTORY, args['eventserver_ip'], int(args['eventserver_port']))

    tests_dict = get_tests(test_context)
    test_names = args['tests']
    tests = []
    if test_names is not None:
        tests = [t for name, t in tests_dict.items() if name in test_names]
    else:
        tests = tests_dict.values()

    # Actual tests execution
    event_server_process = srun_bg('pio eventserver --ip {} --port {}'
            .format(test_context.es_ip, test_context.es_port))
    result = xmlrunner.XMLTestRunner(verbosity=2).run(unittest.TestSuite(tests))
    event_server_process.kill()

    if not result.wasSuccessful():
        sys.exit(1)
