from waapi_helpers import (
    get_guid_of_path, get_object, create_objects, walk_wproj,
    begin_undo_group, end_undo_group, perform_undo, cancel_undo_group, create_bank, get_bank_inclusions_guids
)

from tests.util import WaapiTestCase


class CreateObjectsTestCase(WaapiTestCase):
    EXISTING_FOLDER_NAME = 'Existing_Folder'

    def setUp(self):
        self.assertTrue(self.client.is_connected())

        self.wwu_guid = get_guid_of_path(self.client, '\\Actor-Mixer Hierarchy\\Test_Create_Objects')
        self.assertTrue(isinstance(self.wwu_guid, str))
        self.assertNotEqual(self.wwu_guid, '')

        self.folder_guid, self.folder_name = get_object(
            self.client,
            f'\\Actor-Mixer Hierarchy\\Test_Create_Objects\\{self.EXISTING_FOLDER_NAME}',
            properties=['id', 'name']
        )
        self.assertIsNotNone(self.folder_guid)
        self.assertIsNotNone(self.folder_name)
        self.assertNotEqual(self.folder_guid, '')
        self.assertNotEqual(self.folder_name, '')

        begin_undo_group(self.client)
        self.perform_undo = True

    def tearDown(self):
        end_undo_group(self.client, 'waapi_helpers_test')
        if self.perform_undo:
            perform_undo(self.client)

        self.wwu_guid = None
        self.folder_guid = None
        self.folder_name = None

    def test__create_objects__deep__inside_existing_folder(self):
        names = [self.EXISTING_FOLDER_NAME, 'RND', 'SND']
        types = ['Folder', 'RandomSequenceContainer', 'Sound']

        created_guids = create_objects(self.client, self.wwu_guid, names, types, 'deep')
        self.assertNotEqual(len(created_guids), 0)
        self.assertTrue(all(guid is not None for guid in created_guids))

        # this also ensures Existing_Folder ID (self.folder_guid) didn't change
        for name, in walk_wproj(self.client, self.folder_guid, properties=['name']):
            self.assertIn(name, names)

    def test__create_objects__wide__together_with_existing_folder(self):
        names = [self.EXISTING_FOLDER_NAME, 'RND', 'SND']
        types = ['Folder', 'RandomSequenceContainer', 'Sound']

        created_guids = create_objects(self.client, self.wwu_guid, names, types, 'wide')
        self.assertNotEqual(len(created_guids), 0)
        self.assertTrue(all(guid is not None for guid in created_guids))

        for name, in walk_wproj(self.client, self.folder_guid, properties=['name']):
            self.assertIn(name, names)

    def test__create_objects__non_seq_args(self):
        guid, = create_objects(self.client, self.wwu_guid, 'Temp_Folder', 'Folder')
        self.assertTrue(isinstance(guid, str))
        self.assertNotEqual(guid, '')

    def test__create_bank__include_existing_folder(self):
        banks_parent = get_guid_of_path(self.client, '\\SoundBanks\\Default Work Unit')
        bank_guid = create_bank(self.client, banks_parent, 'Test_Bank', [self.folder_guid])
        self.assertIsNotNone(bank_guid)

        incl_guids = get_bank_inclusions_guids(self.client, bank_guid)
        self.assertEqual(len(incl_guids), 1)
        self.assertEqual(incl_guids[0], self.folder_guid)
