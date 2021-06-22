from waapi import WaapiClient

from waapi_helpers import *

with WaapiClient() as client:
    for event_guid, in walk_wproj(client, '\\Events', ['id'], ['Event']):
        children = [guid for guid, in walk_wproj(client, event_guid)
                    if guid is not None]
        if len(children) == 0:
            delete_object(client, event_guid)
