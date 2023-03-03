# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: iss_message.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from . import ndarray_pb2 as ndarray__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='iss_message.proto',
  package='',
  syntax='proto3',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x11iss_message.proto\x1a\rndarray.proto\"X\n\nIssMessage\x12\x16\n\trequestId\x18\x01 \x01(\tH\x00\x88\x01\x01\x12\x1b\n\x04\x64\x61ta\x18\x02 \x01(\x0b\x32\x08.ndarrayH\x01\x88\x01\x01\x42\x0c\n\n_requestIdB\x07\n\x05_datab\x06proto3'
  ,
  dependencies=[ndarray__pb2.DESCRIPTOR,])




_ISSMESSAGE = _descriptor.Descriptor(
  name='IssMessage',
  full_name='IssMessage',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='requestId', full_name='IssMessage.requestId', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='data', full_name='IssMessage.data', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
    _descriptor.OneofDescriptor(
      name='_requestId', full_name='IssMessage._requestId',
      index=0, containing_type=None,
      create_key=_descriptor._internal_create_key,
    fields=[]),
    _descriptor.OneofDescriptor(
      name='_data', full_name='IssMessage._data',
      index=1, containing_type=None,
      create_key=_descriptor._internal_create_key,
    fields=[]),
  ],
  serialized_start=36,
  serialized_end=124,
)

_ISSMESSAGE.fields_by_name['data'].message_type = ndarray__pb2._NDARRAY
_ISSMESSAGE.oneofs_by_name['_requestId'].fields.append(
  _ISSMESSAGE.fields_by_name['requestId'])
_ISSMESSAGE.fields_by_name['requestId'].containing_oneof = _ISSMESSAGE.oneofs_by_name['_requestId']
_ISSMESSAGE.oneofs_by_name['_data'].fields.append(
  _ISSMESSAGE.fields_by_name['data'])
_ISSMESSAGE.fields_by_name['data'].containing_oneof = _ISSMESSAGE.oneofs_by_name['_data']
DESCRIPTOR.message_types_by_name['IssMessage'] = _ISSMESSAGE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

IssMessage = _reflection.GeneratedProtocolMessageType('IssMessage', (_message.Message,), {
  'DESCRIPTOR' : _ISSMESSAGE,
  '__module__' : 'iss_message_pb2'
  # @@protoc_insertion_point(class_scope:IssMessage)
  })
_sym_db.RegisterMessage(IssMessage)


# @@protoc_insertion_point(module_scope)