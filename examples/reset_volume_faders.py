from waapi import WaapiClient

from waapi_helpers import *

with WaapiClient() as client:
    for bus_guid, bus_notes in walk_wproj(client, '\\Master-Mixer Hierarchy',
                                          properties=['id', 'notes'], types=['Bus', 'AuxBus']):
        if '@wh_ignore' not in bus_notes:
            set_property_value(client, bus_guid, 'BusVolume', 0)

    for am_guid, am_notes, in walk_wproj(client, '\\Actor-Mixer Hierarchy',
                                         properties=['id', 'notes'], types=['ActorMixer']):
        if '@wh_ignore' not in am_notes:
            set_property_value(client, am_guid, 'Volume', 0)
