# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: chia.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='chia.proto',
  package='sharebase',
  syntax='proto2',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\nchia.proto\x12\tsharebase\"\xb1\x02\n\tFarmerMsg\x12\x12\n\nlauncherid\x18\x01 \x02(\t\x12\x1b\n\x13singletonpuzzlehash\x18\x02 \x01(\t\x12\x11\n\tdelaytime\x18\x03 \x01(\x04\x12\x17\n\x0f\x64\x65laypuzzlehash\x18\x04 \x01(\t\x12\x1f\n\x17\x61uthenticationpublickey\x18\x05 \x01(\x0c\x12\x14\n\x0csingletontip\x18\x06 \x01(\x0c\x12\x19\n\x11singletontipstate\x18\x07 \x01(\x0c\x12\x0e\n\x06points\x18\x08 \x01(\x04\x12\x12\n\ndifficulty\x18\t \x01(\x04\x12\x1a\n\x12payoutinstructions\x18\n \x01(\t\x12\x14\n\x0cispoolmember\x18\x0b \x01(\x08\x12\x11\n\ttimestamp\x18\x0c \x01(\x04\x12\x0c\n\x04\x66lag\x18\r \x01(\r\"E\n\x08ShareMsg\x12\x12\n\nlauncherid\x18\x01 \x02(\t\x12\x12\n\ndifficulty\x18\x02 \x01(\x04\x12\x11\n\ttimestamp\x18\x03 \x01(\x04'
)




_FARMERMSG = _descriptor.Descriptor(
  name='FarmerMsg',
  full_name='sharebase.FarmerMsg',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='launcherid', full_name='sharebase.FarmerMsg.launcherid', index=0,
      number=1, type=9, cpp_type=9, label=2,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='singletonpuzzlehash', full_name='sharebase.FarmerMsg.singletonpuzzlehash', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='delaytime', full_name='sharebase.FarmerMsg.delaytime', index=2,
      number=3, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='delaypuzzlehash', full_name='sharebase.FarmerMsg.delaypuzzlehash', index=3,
      number=4, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='authenticationpublickey', full_name='sharebase.FarmerMsg.authenticationpublickey', index=4,
      number=5, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=b"",
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='singletontip', full_name='sharebase.FarmerMsg.singletontip', index=5,
      number=6, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=b"",
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='singletontipstate', full_name='sharebase.FarmerMsg.singletontipstate', index=6,
      number=7, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=b"",
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='points', full_name='sharebase.FarmerMsg.points', index=7,
      number=8, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='difficulty', full_name='sharebase.FarmerMsg.difficulty', index=8,
      number=9, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='payoutinstructions', full_name='sharebase.FarmerMsg.payoutinstructions', index=9,
      number=10, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='ispoolmember', full_name='sharebase.FarmerMsg.ispoolmember', index=10,
      number=11, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='timestamp', full_name='sharebase.FarmerMsg.timestamp', index=11,
      number=12, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='flag', full_name='sharebase.FarmerMsg.flag', index=12,
      number=13, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
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
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=26,
  serialized_end=331,
)


_SHAREMSG = _descriptor.Descriptor(
  name='ShareMsg',
  full_name='sharebase.ShareMsg',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='launcherid', full_name='sharebase.ShareMsg.launcherid', index=0,
      number=1, type=9, cpp_type=9, label=2,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='difficulty', full_name='sharebase.ShareMsg.difficulty', index=1,
      number=2, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='timestamp', full_name='sharebase.ShareMsg.timestamp', index=2,
      number=3, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
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
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=333,
  serialized_end=402,
)

DESCRIPTOR.message_types_by_name['FarmerMsg'] = _FARMERMSG
DESCRIPTOR.message_types_by_name['ShareMsg'] = _SHAREMSG
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

FarmerMsg = _reflection.GeneratedProtocolMessageType('FarmerMsg', (_message.Message,), {
  'DESCRIPTOR' : _FARMERMSG,
  '__module__' : 'chia_pb2'
  # @@protoc_insertion_point(class_scope:sharebase.FarmerMsg)
  })
_sym_db.RegisterMessage(FarmerMsg)

ShareMsg = _reflection.GeneratedProtocolMessageType('ShareMsg', (_message.Message,), {
  'DESCRIPTOR' : _SHAREMSG,
  '__module__' : 'chia_pb2'
  # @@protoc_insertion_point(class_scope:sharebase.ShareMsg)
  })
_sym_db.RegisterMessage(ShareMsg)


# @@protoc_insertion_point(module_scope)