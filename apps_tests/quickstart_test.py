import os
import unittest
import random
from pio_tests.integration import BaseTestCase, AppContext
from utils import AppEngine, srun, pjoin

def read_events(file_path):
    RATE_ACTIONS_DELIMITER = "::"
    SEED = 3
    with open(file_path, 'r') as f:
        events = []
        for line in f:
            data = line.rstrip('\r\n').split(RATE_ACTIONS_DELIMITER)
            if random.randint(0, 1) == 1:
                events.append( {
                        "event": "rate",
                        "entityType": "user",
                        "entityId": 'u' + data[0],
                        "targetEntityType": "item",
                        "targetEntityId": data[1],
                        "properties": { "rating" : float(data[2]) } })
            else:
                events.append({
                    "event": "buy",
                    "entityType": "user",
                    "entityId": data[0],
                    "targetEntityType": "item",
                    "targetEntityId": data[1] })

        return events


class QuickStartTest(BaseTestCase):

    def setUp(self):
        template_path = pjoin(
                self.test_context.engine_directory, "recommendation-engine")
        engine_json_path = pjoin(
                self.test_context.data_directory, "quickstart_test/engine.json")

        self.training_data_path = pjoin(
                self.test_context.data_directory,
                "quickstart_test/training_data.txt")

        # downloading training data
        srun('curl https://raw.githubusercontent.com/apache/spark/master/' \
                'data/mllib/sample_movielens_data.txt --create-dirs -o {}'
                .format(self.training_data_path))

        app_context = AppContext(
                name="MyRecommender",
                template=template_path,
                engine_json_path=engine_json_path)

        self.app = AppEngine(self.test_context, app_context)
        self.app_pid = None

    def runTest(self):
        self.app.new()

        event1 = {
            "event" : "rate",
            "entityType" : "user",
            "entityId" : "u0",
            "targetEntityType" : "item",
            "targetEntityId" : "i0",
            "properties" : {
                "rating" : 5
                },
            "eventTime" : "2014-11-02T09:39:45.618-08:00" }

        event2 = {
            "event" : "buy",
            "entityType" : "user",
            "entityId" : "u1",
            "targetEntityType" : "item",
            "targetEntityId" : "i2",
            "eventTime" : "2014-11-10T12:34:56.123-08:00" }

        self.assertListEqual(
                [201, 201],
                [self.app.send_event(e).status_code for e in [event1, event2]])

        r = self.app.get_events()
        self.assertEquals(200, r.status_code)
        stored_events = r.json()
        self.assertEqual(2, len(stored_events))

        new_events = read_events(self.training_data_path)
        for ev in new_events:
            r = self.app.send_event(ev)
            self.assertEqual(201, r.status_code)

        r = self.app.get_events(params={'limit': -1})
        self.assertEquals(200, r.status_code)
        stored_events = r.json()
        self.assertEquals(len(new_events) + 2, len(stored_events))

        self.app.build()
        self.app.train()
        self.app.deploy(wait_time=15)

        user_query = { "user": 1, "num": 4 }
        r = self.app.query(user_query)
        self.assertEqual(200, r.status_code)
        result = r.json()
        self.assertEqual(4, len(result['itemScores']))

    def tearDown(self):
        self.app.stop()
        self.app.delete_data()
        self.app.delete()
