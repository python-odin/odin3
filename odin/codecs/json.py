import json

from typing import Any, TextIO

from ..bases import DocumentCodec 


class JsonCodec(DocumentCodec):
    """
    JSON Codec
    """
    content_type = 'application/json'

    def __init__(self, allow_nan: bool=True, indent: int=None, sort_keys: bool=False):
        self._encoder = json.JSONEncoder(
            allow_nan=allow_nan, sort_keys=sort_keys, indent=indent,
            default=self._encoder_default
        )
        self._decoder = json.JSONDecoder(
            object_hook=self._decoder_object_hook,
            # Let odin parse these!
            parse_float=str, parse_int=str, parse_constant=str
        )

    def _encoder_default(self, obj: Any):
        raise TypeError()

    def _decoder_object_hook(self, obj: dict):
        return obj

    def dump(self, fp: TextIO, obj: Any) -> None:
        """
        Dump an object/resource to JSON file (or file like) object
        """
        for chunk in self._encoder.iterencode(obj):
            fp.write(chunk)

    def dumps(self, obj: Any) -> str:
        """
        Dump an object/resource to a string.
        """
        return self._encoder.encode(obj)

    def load(self, fp: TextIO):
        pass

    def loads(self, data: str):
        pass


codec = JsonCodec()

dump = codec.dump
dumps = codec.dumps
load = codec.load
loads = codec.loads
