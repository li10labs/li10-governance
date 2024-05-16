import argparse
import boto3
import json
import logging
from datetime import datetime

def setup_logging(log_level):
    """
    Configure logging level.
    """
    logging.basicConfig(level=log_level)
    return logging.getLogger(__name__)

def parse_arguments():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description="Send JSON payload to EventBridge.")
    parser.add_argument("--trail-event", default="./trail_event.json", help="Path to JSON file containing event details.")
    parser.add_argument("--event-bus", default="cloud-custodian-bus", help="Name of the EventBridge bus to send the event to")
    parser.add_argument("--region", default="us-east-1", help="AWS region to use")
    parser.add_argument("--profile", default=None, help="AWS profile to use")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Logging level")
    return parser.parse_args()

def read_event_from_file(file_path):

    try:
        with open(file_path, 'r') as file:
            event_detail = json.load(file)
    except FileNotFoundError:
        logger.error("File not found. Please provide a valid JSON file path.")
    except json.JSONDecodeError:
        logger.error("Invalid JSON format in the provided file.")

    return event_detail

def send_eventbridge_event(event_detail, event_bus_name, region, profile):
    # Initialize the EventBridge client with the specified event bus name
    session = boto3.Session(region_name=region, profile_name=profile)
    client = session.client('events')

    try:
        # Get the ARN of the EventBridge bus
        event_bus_arn = client.describe_event_bus(Name=event_bus_name)['Arn']
        logging.debug(f"EventBridge bus '{event_bus_name}' has arn of: {event_bus_arn}")
    except client.exceptions.ResourceNotFoundException as e:
        logging.error(f"EventBridge bus '{event_bus_name}' not found: {e}")
        return

    # Define the event details
    event = {
        'Entries': [{
            'Time': datetime.now().isoformat(),
            'Source': 'local.test',
            'DetailType': 'AWS API Call via CloudTrail',
            'Detail': json.dumps(event_detail),
            'EventBusName': event_bus_arn
        }]
    }

    # Send the event to the specified EventBridge bus
    response = client.put_events(Entries=event['Entries'])

    # Check the response
    if response['FailedEntryCount'] == 0:
        logging.info(f"Event sent successfully to EventBridge bus '{event_bus_name}'.")
    else:
        logging.error(f"Failed to send event to EventBridge bus '{event_bus_name}': {response['Entries']}")


if __name__ == "__main__":
    args = parse_arguments()
    logger = setup_logging(args.log_level)
    event_detail = read_event_from_file(args.trail_event)

    send_eventbridge_event(event_detail, args.event_bus, args.region, args.profile)
