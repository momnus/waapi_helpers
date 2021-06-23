from waapi import WaapiClient

from waapi_helpers import *

with WaapiClient() as client:
    # after we delete an object, walk_proj will try
    # to find children using its saved ID; WampClientAutobahn
    # will log lots of errors to console, which we don't want,
    # note: use this trick only with tested code
    old_log_level = suppress_waapi_logs()

    for event_guid, in walk_wproj(client, '\\Events', ['id'], ['Event']):
        children = [guid for guid, in walk_wproj(client, event_guid)
                    if guid is not None]
        if len(children) == 0:
            delete_object(client, event_guid)

    set_waapi_log_level(old_log_level)
