from waapi_helpers import get_object, get_guid_of_path, walk_wproj, get_bus_guid_from_name

from tests.util import WaapiTestCase


class WprojWalkTestCase(WaapiTestCase):
    def setUp(self):
        self.assertTrue(self.client.is_connected())
        self.wwu_guid = get_guid_of_path(self.client, '\\Actor-Mixer Hierarchy\\Test_Walk_Wproj')
        wwu_name, = get_object(self.client, self.wwu_guid, properties=['name'])
        self.assertEqual(wwu_name, 'Test_Walk_Wproj')

    def tearDown(self):
        self.wwu_guid = None

    def test__get_guid_of_path__am_hierarchy(self):
        guid = get_guid_of_path(self.client, '\\Actor-Mixer Hierarchy')
        self.assertTrue(isinstance(guid, str))
        self.assertTrue(guid != '')

    def test__walk_wproj__test_walk_wwu__walked_all_objects(self):
        obj_names = {
            'AM_01', 'AM_02',
            'RND_01', 'RND_02', 'RND_03', 'RND_04',
            'SND_01', 'SND_02', 'SND_03', 'SND_04', 'SND_05', 'SND_06',
            'SND_07', 'SND_08', 'SND_09', 'SND_10', 'SND_11',
        }

        # didn't test depth-first order, because iteration order in WAAPI is undefined

        for name, in walk_wproj(self.client, self.wwu_guid, properties=['name']):
            self.assertIn(name, obj_names)
            obj_names.remove(name)

        self.assertEqual(len(obj_names), 0)

    def test__walk_wproj__test_walk_wwu__walked_only_sounds(self):
        obj_names = {
            'SND_01', 'SND_02', 'SND_03', 'SND_04', 'SND_05', 'SND_06',
            'SND_07', 'SND_08', 'SND_09', 'SND_10', 'SND_11',
        }

        for name, in walk_wproj(self.client, self.wwu_guid, types=['Sound'], properties=['name']):
            self.assertIn(name, obj_names)
            obj_names.remove(name)

        self.assertEqual(len(obj_names), 0)

    def test__walk_wproj__test_walk_wwu__walked_only_am_and_rnd(self):
        obj_names = {
            'AM_01', 'AM_02',
            'RND_01', 'RND_02', 'RND_03', 'RND_04',
        }

        for name, in walk_wproj(self.client, self.wwu_guid,
                                types=['ActorMixer', 'RandomSequenceContainer'],
                                properties=['name']):
            self.assertIn(name, obj_names)
            obj_names.remove(name)

        self.assertEqual(len(obj_names), 0)

    def test__walk_wproj__non_seq_args__yield_correct_guids_and_names(self):
        walked_am = False
        for guid, in walk_wproj(self.client, self.wwu_guid, 'id', 'ActorMixer'):
            walked_am = True
            self.assertEqual(len(guid), 38)
            self.assertTrue(guid.startswith('{'))
            self.assertTrue(guid.endswith('}'))
        self.assertTrue(walked_am)

        walked_rnd_cont = False
        for name, in walk_wproj(self.client, self.wwu_guid, 'name', 'RandomSequenceContainer'):
            walked_rnd_cont = True
            self.assertTrue(name.startswith('RND_'))
        self.assertTrue(walked_rnd_cont)

    def test__get_bus_guid_from_name__master_audio_bus(self):
        guid = get_bus_guid_from_name(self.client, 'Master Audio Bus')
        self.assertIsNotNone(guid)
        self.assertTrue(isinstance(guid, str))
        self.assertTrue(guid != '')
