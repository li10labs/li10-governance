from c7n import handler

def run(event, context):
    return handler.dispatch_event(event, context)