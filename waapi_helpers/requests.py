import copy
import os
import typing as _t
import waapi as _w
from . import constants as _c

# ------------------------------------------

_OnNameConflict3 = _t.Union[_t.Literal['rename'], _t.Literal['replace'], _t.Literal['fail']]
_OnNameConflict4 = _t.Union[_t.Literal['rename'], _t.Literal['replace'], _t.Literal['fail'], _t.Literal['merge']]
_InclusionOperation = _t.Union[_t.Literal['add'], _t.Literal['remove'], _t.Literal['replace']]
_ImportOperation = _t.Union[_t.Literal['createNew'], _t.Literal['useExisting'], _t.Literal['replaceExisting']]
_WaapiValue = _t.Any  # TODO: specify typing
_GetObjectReturn = _t.Tuple[_WaapiValue, ...]
_CreateObjectsMethod = _t.Union[_t.Literal['wide'], _t.Literal['deep']]
_StrOrSeqOfStr = _t.Union[str, _t.Sequence[str]]


def _check_client(client: _w.WaapiClient) -> bool:
    return client is not None and client.is_connected()


def _check_properties(properties: _t.Sequence[str]) -> bool:
    return properties is not None and isinstance(properties, list)


def _check_fields(obj: dict, *fields: str) -> bool:
    if not isinstance(obj, dict):
        return False
    return all(f in obj for f in fields)


def _check_get_ret(ret: _t.Dict[str, _t.Any]) -> bool:
    return _check_fields(ret, 'return') and len(ret['return']) > 0


def _iter_dict_depth(d: _t.Dict[_t.Any, _t.Any], key: _t.Any) -> _t.Iterator:
    if d is None:
        return
    root = d
    yield root
    while key in root:
        root = root[key]
        yield root


def _get_filename(path: str) -> str:
    return os.path.splitext(os.path.basename(path))


def _is_seq(x):
    return hasattr(x, '__iter__')


def _ensure_str_list(x: _StrOrSeqOfStr, ignore=None) -> _t.List[str]:
    if ignore is not None and x == ignore:
        return x

    if isinstance(x, str):
        return [x]
    elif _is_seq(x):
        return [i for i in x]
    else:
        raise ValueError("Invalid type of argument 'x'")


def _is_any_val_none(*args):
    return not all(args)


# ------------------------------------------

def get_object(client: _w.WaapiClient,
               guid_or_path: str,
               properties: _t.Sequence[str] = None) -> _GetObjectReturn:
    if properties is None:
        properties = ['id']

    assert _check_client(client)
    assert _check_properties(properties)
    assert guid_or_path is not None

    is_path = guid_or_path.startswith('\\')
    from_key = 'path' if is_path else 'id'
    query = {'from': {from_key: [guid_or_path]}}

    ret = client.call(_c.core_object_get, query, options={'return': properties})

    if _check_get_ret(ret):
        obj = ret['return'][0]
        return tuple(obj.get(p, None) for p in properties)
    else:
        return tuple(None for _ in properties)


def get_name_of_guid(client: _w.WaapiClient, guid: str) -> _t.Optional[str]:
    value, = get_object(client, guid, ['name'])
    return value if value is not None else None


def get_path_of_guid(client: _w.WaapiClient, guid: str) -> _t.Optional[str]:
    value, = get_object(client, guid, ['path'])
    return value if value is not None else None


def get_guid_of_path(client: _w.WaapiClient, path: str) -> _t.Optional[str]:
    value, = get_object(client, path, ['id'])
    return value if value is not None else None


def get_name_of_path(client: _w.WaapiClient, path: str) -> _t.Optional[str]:
    value, = get_object(client, path, ['name'])
    return value if value is not None else None


def get_parent_guid(client: _w.WaapiClient, obj_guid) -> _t.Optional[str]:
    query = {
        'from': {'id': [obj_guid]},
        'transform': [{'select': ['parent']}]
    }
    ret = client.call(_c.core_object_get, query, options={'return': ['id']})
    if _check_get_ret(ret):
        return ret['return'][0]['id']
    else:
        return None


def get_property_names(client: _w.WaapiClient, obj_guid: str) -> _t.Sequence[str]:
    ret = client.call(_c.core_object_get_prop_and_ref_names,
                      {'object': obj_guid})
    if _check_fields(ret, 'return'):
        return ret['return']
    else:
        return []


def get_property_value(client: _w.WaapiClient,
                       object_guid: str,
                       property_name: str) -> _t.Optional[_WaapiValue]:
    value, = get_object(client, object_guid, properties=[property_name])
    return value


def get_bus_guid_from_name(client: _w.WaapiClient,
                           bus_name: str) -> _t.Optional[str]:
    for guid, name in walk_wproj(client, '\\Master-Mixer Hierarchy', ['id', 'name'], ['Bus']):
        if name == bus_name:
            return guid
    return None


def set_property_value(client: _w.WaapiClient,
                       object_guid: str,
                       property_name: str,
                       value: _WaapiValue):
    if value is None:
        return
    client.call(_c.core_object_set_property, {'object': object_guid,
                                              'property': property_name,
                                              'value': value})


# ------------------------------------------

def _walk_depth_first(client, start, props, ret_props, types):
    query = {
        'from': {'path': [start]} if start.startswith('\\') else {'id': [start]},
        'transform': [{'select': ['children']}]
    }

    ret = client.call(_c.core_object_get, query, options={'return': props})
    if not _check_get_ret(ret):
        return

    for obj in ret['return']:
        if types == 'any' or obj['type'] in types:
            yield tuple(obj[p] for p in ret_props)
        yield from _walk_depth_first(client, obj['id'], props, ret_props, types)


def walk_wproj(client: _w.WaapiClient,
               start_guids_or_paths: _StrOrSeqOfStr,
               properties: _t.Sequence[str] = None,
               types: _t.Union[_t.Sequence[str], _t.Literal['any']] = 'any') -> _t.Iterator[_t.Tuple[_WaapiValue]]:
    if properties is None:
        properties = ['id']

    if not _check_client(client):
        raise ValueError('Waapi client is none or disconnected')
    if _is_any_val_none(start_guids_or_paths, types):
        return ValueError('start_guids_or_path and types cannot be None')

    start_list = _ensure_str_list(start_guids_or_paths)
    props = _ensure_str_list(properties)
    req_types = _ensure_str_list(types, 'any')

    ret_props = copy.copy(props)
    for p in 'id', 'type':
        if p not in props:
            props.append(p)

    for start in start_list:
        yield from _walk_depth_first(client, start, props, ret_props, req_types)


# ------------------------------------------

def _create_objects__deep(client, parent, names, types, on_name_conflict):
    query = {
        'parent': parent,
        'onNameConflict': on_name_conflict
    }

    first = True
    root = query
    for obj_name, obj_type in zip(names, types):
        if first:
            first = False
        else:
            root['children'] = [{}]
            root = root['children'][0]
        root['name'] = obj_name
        root['type'] = obj_type

    ret = client.call(_c.core_object_create, query)
    if _check_fields(ret, 'id'):
        return [obj['id'] for obj in _iter_dict_depth(ret, 'children') if 'id' in obj]
    else:
        return []


def _create_objects__wide(client, parent, names, types, on_name_conflict):
    created_guids = []
    for obj_name, obj_type in zip(names, types):
        obj = client.call(_c.core_object_create, {
            'parent': parent,
            'onNameConflict': on_name_conflict,
            'name': obj_name,
            'type': obj_type
        })

        if _check_fields(obj, 'id'):
            created_guids.append(obj['id'])
        else:
            created_guids.append(None)
    return created_guids


def create_objects(client: _w.WaapiClient,
                   parent_guid_or_path: _t.Optional[str],
                   names: _t.Sequence[str],
                   types: _t.Sequence[str],
                   method: _CreateObjectsMethod = 'wide',
                   on_name_conflict: _OnNameConflict4 = 'merge') -> _t.Sequence[_t.Optional[str]]:
    if names is None or types is None:
        return []

    assert _check_client(client)
    assert parent_guid_or_path
    assert len(names) == len(types)

    if len(names) == 0:
        return []

    if method == 'wide':
        return _create_objects__wide(client, parent_guid_or_path, names, types, on_name_conflict)
    elif method == 'deep':
        return _create_objects__deep(client, parent_guid_or_path, names, types, on_name_conflict)
    else:
        assert False, "create_objects method be either 'wide' or 'deep'"


def create_bank(client: _w.WaapiClient,
                parent_guid: str,
                bank_name: str,
                inclusion_guids: _t.Sequence[str],
                inclusion_op: _InclusionOperation = 'replace',
                inclusion_filter=None,
                on_name_conflict: _OnNameConflict4 = 'merge') -> _t.Optional[str]:
    assert len(inclusion_guids) > 0

    bank_guids = create_objects(client, parent_guid, [bank_name], ['SoundBank'],
                                on_name_conflict=on_name_conflict)
    if bank_guids is None or len(bank_guids) < 1 or bank_guids[0] is None:
        return None

    set_bank_inclusions(client, bank_guids[0], inclusion_guids, inclusion_op, inclusion_filter)
    return bank_guids[0]


def get_bank_inclusions_guids(client: _w.WaapiClient, bank: str) -> _t.Sequence[str]:
    ret = client.call(_c.core_soundbank_get_inclusions, {'soundbank': bank})
    if _check_fields(ret, 'inclusions'):
        return [incl['object'] for incl in ret['inclusions']]
    else:
        return []


def set_bank_inclusions(client: _w.WaapiClient,
                        bank_guid: str,
                        inclusion_guids: _t.Sequence[str],
                        inclusion_op: _InclusionOperation = 'replace',
                        inclusion_filter: _t.Sequence[str] = None):
    if inclusion_filter is None:
        inclusion_filter = ['events', 'structures', 'media']
    client.call(_c.core_soundbank_set_inclusions,
                {'operation': inclusion_op, 'soundbank': bank_guid,
                 'inclusions': [{'object': guid, 'filter': inclusion_filter}
                                for guid in inclusion_guids]})


def _copy_or_move_object(client: _w.WaapiClient,
                         uri: str,
                         copy_from: str,
                         new_parent: str,
                         on_name_conflict: _OnNameConflict3 = 'fail') -> _t.Optional[str]:
    assert _check_client(client)

    ret = client.call(uri, {'object': copy_from,
                            'parent': new_parent,
                            'onNameConflict': on_name_conflict})

    if _check_fields(ret, 'id'):
        return ret['id']
    else:
        return None


def copy_object(client: _w.WaapiClient,
                copy_from: str,
                new_parent: str,
                on_name_conflict: _OnNameConflict3 = 'fail') -> _t.Optional[str]:
    return _copy_or_move_object(client, _c.core_object_copy,
                                copy_from, new_parent, on_name_conflict)


def move_object(client: _w.WaapiClient,
                copy_from: str,
                new_parent: str,
                on_name_conflict: _OnNameConflict3 = 'fail') -> _t.Optional[str]:
    return _copy_or_move_object(client, _c.core_object_move,
                                copy_from, new_parent, on_name_conflict)


def delete_object(client: _w.WaapiClient, guid: str):
    client.call(_c.core_object_delete, {'object': guid})


def copy_properties(client: _w.WaapiClient,
                    copy_from_guid: str,
                    copy_to_guid: str):
    # Does not copy references

    src_names = set(get_property_names(client, copy_from_guid))
    target_names = set(get_property_names(client, copy_to_guid))

    for prop in src_names.intersection(target_names):
        v = get_property_value(client, copy_from_guid, prop)
        is_reference = isinstance(v, dict)
        if not is_reference:
            set_property_value(client, copy_to_guid, prop, v)


# ------------------------------------------

def import_audio(client: _w.WaapiClient,
                 parent_guid: str,
                 wav_files: _t.Sequence[str],
                 import_operation: _ImportOperation = 'useExisting',
                 orig_subfolder: str = '',
                 is_voice: bool = False):
    tag = '<Voice>' if is_voice else '<Sound>'  # haven't tested this one actually
    query = {
        'default': {
            'importOperation': import_operation,
            'importLocation': parent_guid,
            'originalsSubFolder': orig_subfolder,
            'imports': [{
                'audioFile': wav,
                'objectPath': tag + _get_filename(wav)
            } for wav in wav_files]
        }
    }
    client.call(_c.core_audio_import, query)


# ------------------------------------------

def begin_undo_group(client: _w.WaapiClient):
    client.call(_c.core_undo_begin_group)


def end_undo_group(client: _w.WaapiClient, display_name: str):
    client.call(_c.core_undo_end_group, {'displayName': display_name})


def cancel_undo_group(client: _w.WaapiClient):
    client.call(_c.core_undo_cancel_group)


def perform_undo(client: _w.WaapiClient):
    client.call(_c.ui_commands_execute, {'command': 'Undo'})


# ------------------------------------------

def get_waapi_log_level():
    return _w.WampClientAutobahn.logger.getEffectiveLevel()


def set_waapi_log_level(level: int):
    return _w.WampClientAutobahn.logger.setLevel(level)


def suppress_waapi_logs(with_level: int = 1000) -> int:
    old_level = get_waapi_log_level()
    set_waapi_log_level(with_level)
    return old_level
