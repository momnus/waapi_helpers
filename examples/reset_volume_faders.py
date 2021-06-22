from waapi import WaapiClient

from waapi_helpers import *

with WaapiClient() as client:
    for bus_guid, in walk_wproj(client, '\\Master-Mixer Hierarchy', types=['Bus', 'AuxBus']):
        set_property_value(client, bus_guid, 'BusVolume', 0)

    for am_guid, in walk_wproj(client, '\\Actor-Mixer Hierarchy', types=['ActorMixer']):
        set_property_value(client, am_guid, 'Volume', 0)
