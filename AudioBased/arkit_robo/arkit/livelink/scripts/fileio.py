# Copyright (c) 2023, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import os
import json
import shutil
import asyncio
import tempfile
from typing import List, Any
import numpy as np

import carb

import omni.usd
from omni.avatar.livelink.scripts.pipe import set_property

NODE_TYPE = "omni.avatar.FloatArrayTuner"
NODE_NAME = "Float Array Tuner"


class OmniClientError(RuntimeError):
    pass


async def load_tuner_preset(filepath: str, primpath: str, **metadata):
    """Load tuner preset from a file.
    """
    data = await load_json(filepath)
    properties = data.get('__properties__', {})
    prim = write_tuner_properties(primpath, **properties)
    return True


def write_tuner_properties(primpath: str, **properties):
    """Write tuner preset properties
    """
    stage = omni.usd.get_context().get_stage()
    prim = stage.GetPrimAtPath(primpath)
    if not prim.IsValid():
        raise ValueError(f'Prim path is not valid: {primpath}')

    for name, values in properties.items():
        attr = prim.GetAttribute(name)
        if not attr.IsValid():
            carb.log_warn(f'Cannot update attribute, {primpath}.{name}.')
            continue
        attr.Set(values)
        if ':gains' in name:
            attr2 = prim.GetAttribute('state:gain_defaults')
            if attr2.IsValid():
                attr2.Set(values)
        elif ':offsets' in name:
            attr2 = prim.GetAttribute('state:offset_defaults')
            if attr2.IsValid():
                attr2.Set(values)
    return prim


async def load_json(filepath: str):
    """
    Returns:
        (Any) json contents

    Raises:
        OmniClientError: raised when file cannot be saved through omni.client
        ImportError: raised when omni.client module is not available
    """
    localfile = tempfile.mktemp(prefix='avatar-')

    remote = False
    if "omniverse://" in filepath.lower():
        try:
            import omni.client
        except ImportError:
            msg = (
                'Nucleus service is not available.'
                ' Please use local storage path.'
            )
            # carb.log_error(msg)
            raise
        remote = True

    if remote:
        result = await copy_omni_file(filepath, localfile)
        if result != omni.client.Result.OK:
            msg = (
                f"Cannot copy from {filepath} to {localfile}."
                f" Error code: {result}."
            )
            # carb.log_error(msg)
            raise OmniClientError(msg)
    else:
        localfile = filepath

    with open(localfile, 'r', encoding='utf-8') as rf:
        data = json.load(rf)

    return data


async def save_tuner_preset(filepath: str, primpath: str, **metadata):
    """Write array tuner data to a file.
    """
    if 'description' not in metadata:
        metadata['description'] = 'A Preset for Float Array Tuner'

    outdata = read_tuner_properties(primpath) or {}
    outdata['__metadata__'] = metadata

    result = await save_json(filepath, outdata)
    return result


def read_tuner_properties(primpath: str):
    stage = omni.usd.get_context().get_stage()
    prim = stage.GetPrimAtPath(primpath)
    if not prim.IsValid():
        raise ValueError(f'Prim path is not valid: {primpath}')

    attrs = ['inputs:names', 'inputs:gains', 'inputs:offsets']
    data = {n: list(prim.GetAttribute(n).Get()) for n in attrs}

    outdata = {
        '__type__': prim.GetAttribute('node:type').Get(),
        '__version__': prim.GetAttribute('node:typeVersion').Get(),
        '__properties__': data,
    }
    return outdata


async def save_json(filepath: str, data: Any):
    """
    Returns:
        (omni.client.Result or True)

    Raises:
        OmniClientError: raised when file cannot be saved through omni.client
        ImportError: raised when omni.client module is not available
    """
    outfile = tempfile.mktemp(prefix='avatar-')
    with open(outfile, 'w', encoding='utf-8') as wf:
        json.dump(data, wf, indent=4)

    remote = False
    if "omniverse://" in filepath.lower():
        try:
            import omni.client
        except ImportError:
            msg = (
                'Nucleus service is not available.'
                ' Please use local storage path.'
            )
            # carb.log_error(msg)
            raise
        remote = True

    if remote:
        result = await copy_omni_file(outfile, filepath)
        if result != omni.client.Result.OK:
            msg = (
                f"Cannot copy from {outfile} to {filepath}."
                f" Error code: {result}."
            )
            # carb.log_error(msg)
            raise OmniClientError(msg)
    else:
        shutil.copy(outfile, filepath, follow_symlinks=True)
        result = os.access(filepath, os.R_OK)

    return result


async def copy_omni_file(source: str, destination: str):
    """Copy a file to a nucleus location.
    Args:
        source: (str) a source file path
        destination: (str) a destination file path

    Returns:
        (omni.client.Result) result status
    """
    try:
        import omni.client
        await omni.client.delete_async(destination)
    except ImportError:
        raise
    finally:
        result = await omni.client.copy_async(source, destination)

    return result
