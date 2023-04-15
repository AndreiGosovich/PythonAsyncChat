import unittest
import server
import sys
import json
from datetime import datetime, timezone
import calendar
from socket import *


class TestGetArguments(unittest.TestCase):
    def testAllArguments(self):
        sys.argv.append('-a localhost')
        sys.argv.append('-p 1111')
        r = server.get_arguments()
        sys.argv.pop()
        sys.argv.pop()
        self.assertEqual(r, (' localhost', 1111))

    def testAddressOnly(self):
        sys.argv.append('-a localhost')
        r = server.get_arguments()
        sys.argv.pop()
        self.assertEqual(r, (' localhost', None))


class TestGetSocket(unittest.TestCase):
    def testTypeSocket(self):
        r = server.get_socket('localhost', 7777)
        r.close()
        self.assertEqual(type(r), socket)

    def testAddressFamily(self):
        r = server.get_socket('localhost', 7777)
        r.close()
        self.assertEqual(r.family, AF_INET)

    def testSocketType(self):
        r = server.get_socket('localhost', 7777)
        r.close()
        self.assertEqual(r.type, SOCK_STREAM)


class TestParseClientData(unittest.TestCase):
    def testFullString(self):
        test_data = {
                        "action": "presence",
                        "time":  calendar.timegm(datetime.now(timezone.utc).utctimetuple()),
                        "type": 'status',
                        "user": {
                            "account_name": 'Andrei',
                            "status": 'online',
                        }
                    }

        r = server.parse_client_data(json.dumps(test_data))

        self.assertEqual(r, test_data)


class TestGetResponse(unittest.TestCase):
    def testPresenceMessage(self):
        test_data = {
            "action": "presence",
            "time": calendar.timegm(datetime.now(timezone.utc).utctimetuple()),
            "type": 'status',
            "user": {
                "account_name": 'Andrei',
                "status": 'online',
            }
        }

        test_response = {
                            "response": 200,
                            "time": calendar.timegm(datetime.now(timezone.utc).utctimetuple()),
                            "alert": 'Ok',
                        }

        r = server.get_response(test_data)

        self.assertEqual(r, json.dumps(test_response))

    def test404(self):
        pass


# Запустить тестирование
if __name__ == '__main__':
    unittest.main()
