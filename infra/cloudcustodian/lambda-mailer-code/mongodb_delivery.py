# Copyright li10
# SPDX-License-Identifier: Apache-2.0
import time
import json
from pymongo import MongoClient

class MongoDBDelivery:
    def __init__(self, config, session, logger):
        self.config = config
        self.logger = logger
        self.session = session
        self.mongodb_uri = self.config.get("mongodb_uri")
        self.mongodb_database = self.config.get("mongodb_database")
        self.mongodb_collection = self.config.get("mongodb_collection")

        # Initialize MongoDB client
        if self.mongodb_uri:
            self.logger.debug("Connecting to MongoDB URI: %s", self.mongodb_uri)
            self.client = MongoClient(self.mongodb_uri)
            self.logger.debug("Connection successful")
            self.db = self.client[self.mongodb_database]
            self.logger.debug("Using database: %s", self.mongodb_database)
            self.collection = self.db[self.mongodb_collection]
            self.logger.debug("Using collection: %s", self.mongodb_collection)

    def deliver_mongodb_messages(self, mongodb_message_packages, sqs_message):
        if len(mongodb_message_packages) > 0:
            self.logger.info(
                "Sending account:{account} policy:{policy} {resource}:{quantity} to MongoDB".format(
                    account=sqs_message.get("account", ""),
                    policy=sqs_message["policy"]["name"],
                    resource=sqs_message["policy"]["resource"],
                    quantity=len(sqs_message["resources"]),
                )
            )

            for message in mongodb_message_packages:
                self.logger.debug("Inserting message into MongoDB: %s", message)
                self.collection.insert_one(message)
                self.logger.debug("Message inserted successfully")

    def get_mongodb_message_packages(self, sqs_message):
        timestamp = time.time()
        mongodb_rendered_messages = []

        decoded_message = json.dumps(sqs_message)
        self.logger.debug("Decoded SQS Message: %s", decoded_message)

        mongodb_message = {
            "_id": {
                "ts": timestamp,
                "execution_id": sqs_message["execution_id"]
            },
            "account_name": sqs_message["account"],
            "account_id": sqs_message["account_id"],
            "region": sqs_message["region"],
            "source": sqs_message["policy"]["resource"],
            "policy": sqs_message["policy"]["filters"],
        }
        if sqs_message.get("event", None) is not None:
            self.logger.debug("SQS message contains event")
            mongodb_message["event"] = sqs_message["event"]["detail"]["eventName"]
            mongodb_message["mode_type"] = sqs_message["policy"]["mode"]["type"]
        else:
            self.logger.debug("SQS message does not contain event")
            mongodb_message["mode_type"] = "scheduled"

        mongodb_rendered_messages.append(mongodb_message)

        return mongodb_rendered_messages
