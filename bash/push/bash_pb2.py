# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: bash.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\nbash.proto\x12\x0cservice_bash\"\x1d\n\x05Point\x12\t\n\x01x\x18\x01 \x01(\x02\x12\t\n\x01y\x18\x02 \x01(\x02\"\xfd\x02\n\x0f\x44\x65tectionResult\x12#\n\x06points\x18\x01 \x03(\x0b\x32\x13.service_bash.Point\x12\x12\n\nclass_name\x18\x02 \x01(\t\x12\x0c\n\x04xmin\x18\x03 \x01(\x02\x12\x0c\n\x04ymin\x18\x04 \x01(\x02\x12\x10\n\x08\x62\x62_width\x18\x05 \x01(\x02\x12\x11\n\tbb_height\x18\x06 \x01(\x02\x12\r\n\x05score\x18\x07 \x01(\x02\x12\x0e\n\x06length\x18\x08 \x01(\x02\x12\r\n\x05width\x18\t \x01(\x02\x12\x12\n\npixel_area\x18\n \x01(\x02\x12\x11\n\tgradients\x18\x0b \x01(\x02\x12\x10\n\x08\x63ontrast\x18\x0c \x01(\x02\x12\x12\n\nbrightness\x18\r \x01(\x02\x12\x17\n\x0fmax20brightness\x18\x0e \x01(\x02\x12\x17\n\x0fmin20brightness\x18\x0f \x01(\x02\x12\x16\n\x0e\x64\x65\x66\x65\x63t_feature\x18\x10 \x01(\t\x12\x12\n\nclass_type\x18\x11 \x01(\t\x12\x17\n\x0f\x64\x65tection_value\x18\x12 \x01(\x02\"\xa4\x05\n\x13ImageRecheckRequest\x12\x14\n\x0c\x61\x63\x63\x65ss_token\x18\x01 \x01(\t\x12\x11\n\tdevice_no\x18\x02 \x01(\t\x12\x14\n\x0cproduct_name\x18\x03 \x01(\t\x12\x17\n\x0foptical_side_id\x18\x04 \x01(\x05\x12\r\n\x05width\x18\x05 \x01(\x05\x12\x0e\n\x06height\x18\x06 \x01(\x05\x12\x15\n\rencoded_image\x18\x07 \x01(\x0c\x12\x14\n\x0cimage_header\x18\x08 \x01(\t\x12-\n\x06result\x18\t \x03(\x0b\x32\x1d.service_bash.DetectionResult\x12\x15\n\rmodel_version\x18\n \x01(\t\x12\x14\n\x0crequest_type\x18\x0b \x01(\t\x12\x0f\n\x07is_crop\x18\x0c \x01(\x05\x12\x35\n\x0e\x64\x65tection_area\x18\r \x03(\x0b\x32\x1d.service_bash.DetectionResult\x12\x1b\n\x13\x64\x65tection_area_type\x18\x0e \x01(\x05\x12\x19\n\x11\x64\x65tection_comment\x18\x0f \x01(\t\x12\x15\n\rproto_version\x18\x10 \x01(\t\x12\x13\n\x0bsystem_type\x18\x11 \x01(\x05\x12\x16\n\x0e\x65xpand_feature\x18\x12 \x01(\t\x12\x14\n\x0cmodel_result\x18\x13 \x01(\t\x12\x12\n\nimage_time\x18\x14 \x01(\t\x12\x14\n\x0crequest_time\x18\x15 \x01(\t\x12\x10\n\x08trace_id\x18\x16 \x01(\t\x12\x19\n\x11\x65ncoded_pcd_model\x18\x17 \x01(\x0c\x12\x1b\n\x13request_detail_time\x18\x18 \x01(\t\x12\x1c\n\x14\x65ncoded_pcd_compress\x18\x19 \x01(\x05\x12!\n\x19\x65ncoded_pcd_compress_type\x18\x1a \x01(\x05\"v\n\x11ImageRecheckReply\x12\x1c\n\x14image_recheck_result\x18\x01 \x01(\t\x12\x14\n\x0cimage_header\x18\x02 \x01(\t\x12-\n\x06result\x18\x03 \x03(\x0b\x32\x1d.service_bash.DetectionResult2c\n\x0b\x42\x61shService\x12T\n\x0cImageRecheck\x12!.service_bash.ImageRecheckRequest\x1a\x1f.service_bash.ImageRecheckReply\"\x00\x42\x08Z\x06./bashb\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bash_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  DESCRIPTOR._serialized_options = b'Z\006./bash'
  _POINT._serialized_start=28
  _POINT._serialized_end=57
  _DETECTIONRESULT._serialized_start=60
  _DETECTIONRESULT._serialized_end=396
  _IMAGERECHECKREQUEST._serialized_start=399
  _IMAGERECHECKREQUEST._serialized_end=872
  _IMAGERECHECKREPLY._serialized_start=874
  _IMAGERECHECKREPLY._serialized_end=992
  _BASHSERVICE._serialized_start=994
  _BASHSERVICE._serialized_end=1093
# @@protoc_insertion_point(module_scope)
