from waapi import WaapiClient

from waapi_helpers import *

with WaapiClient() as client:
    for action_guid, action_ref in walk_wproj(client, '\\Events', ['id', '@Target'], ['Action']):
        ref_obj, = get_object(client, action_ref['id'])
        if ref_obj is None:
            delete_object(client, action_guid)
