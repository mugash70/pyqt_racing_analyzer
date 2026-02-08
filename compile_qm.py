#!/usr/bin/env python3
"""Compile .ts to .qm using Python XML parsing"""
import xml.etree.ElementTree as ET
import struct
import os

def compile_ts_to_qm(ts_file, qm_file):
    # Read and fix the TS file content first
    with open(ts_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix unescaped ampersands in source strings
    content = content.replace('Settings & Data Management', 'Settings & Data Management')
    
    # Parse the fixed content
    try:
        root = ET.fromstring(content.encode('utf-8'))
    except Exception as e:
        print(f"Error parsing XML: {e}")
        print("Debug content around line 150:")
        lines = content.split('\n')
        for i, line in enumerate(lines[140:160]):
            print(f"{140+i}: {line}")
        return
    
    translations = {}
    for context in root.findall('context'):
        context_name = context.find('name').text
        for message in context.findall('message'):
            source = message.find('source')
            translation = message.find('translation')
            if source is not None and translation is not None and translation.text:
                key = f"{context_name}::{source.text}"
                translations[key] = translation.text
    
    with open(qm_file, 'wb') as f:
        f.write(b'\x3c\xb8\x64\x18\x00\x00\x00\x00')
        for key, value in translations.items():
            context, source = key.split('::', 1)
            f.write(struct.pack('<I', len(context.encode('utf-8'))))
            f.write(context.encode('utf-8'))
            f.write(struct.pack('<I', len(source.encode('utf-8'))))
            f.write(source.encode('utf-8'))
            f.write(struct.pack('<I', len(value.encode('utf-8'))))
            f.write(value.encode('utf-8'))

if __name__ == '__main__':
    ts_path = 'i18n/zh_HK.ts'
    qm_path = 'i18n/zh_HK.qm'
    compile_ts_to_qm(ts_path, qm_path)
    print(f"Compiled {ts_path} to {qm_path}")