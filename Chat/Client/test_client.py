import unittest
from Chat.Client import client
import sys
import json
from datetime import datetime, timezone
import calendar
from socket import socket, AF_INET, SOCK_STREAM


class TestGetArguments(unittest.TestCase):
    def testError(self):
        self.assertRaises(SystemExit, client.get_arguments)

    def testAllArguments(self):
        sys.argv.append('localhost')
        sys.argv.append('1111')
        r = client.get_arguments()
        sys.argv.pop()
        sys.argv.pop()
        self.assertEqual(r, ('localhost', 1111))

    def testAddressOnly(self):
        sys.argv.append('localhost')
        r = client.get_arguments()
        sys.argv.pop()
        self.assertEqual(r, ('localhost', 0))


class TestCreatePresenceMessage(unittest.TestCase):
    def testFullString(self):
        r = client.create_presence_message('Andrei', 'someStatus', 'someType')
        data = {
                    "action": "presence",
                    "time":  calendar.timegm(datetime.now(timezone.utc).utctimetuple()),
                    "type": "someType",
                    "user": {
                        "account_name": "Andrei",
                        "status": "someStatus",
                    }
                }
        self.assertEqual(r, json.dumps(data))


class TestParseServerResponse(unittest.TestCase):
    def testFullString(self):
        test_data = {
                "response": 200,
                "time": calendar.timegm(datetime.now(timezone.utc).utctimetuple()),
                "alert": 'Ok',
            }

        r = client.parse_server_response(json.dumps(test_data))

        self.assertEqual(r, test_data)


class TestGetSocket(unittest.TestCase):
    def testTypeSocket(self):
        r = client.get_socket(AF_INET, SOCK_STREAM)
        r.close()
        self.assertEqual(type(r), socket)

    def testAddressFamily(self):
        r = client.get_socket(AF_INET, SOCK_STREAM)
        r.close()
        self.assertEqual(r.family, AF_INET)

    def testSocketType(self):
        r = client.get_socket(AF_INET, SOCK_STREAM)
        r.close()
        self.assertEqual(r.type, SOCK_STREAM)


# Запустить тестирование
if __name__ == '__main__':
    unittest.main()
