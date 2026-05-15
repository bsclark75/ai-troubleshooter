incident_queue = []
active_incidents = {}

def add_to_queue(incident):

    incident_queue.append(incident)

    active_incidents[
        incident["incident_id"]
    ] = incident
def get_queue():

    return incident_queue

def pop_queue():

    if incident_queue:

        return incident_queue.pop(0)

    return None

def get_active_incident(incident_id):

    return active_incidents.get(
        incident_id
    )