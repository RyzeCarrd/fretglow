"""Prepare local firmware assets from a compiled, configured Santroller extension."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import brotli

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--firmware',type=Path,required=True)
    parser.add_argument('--picotool',type=Path,required=True)
    parser.add_argument('--original-config',type=Path,required=True)
    parser.add_argument('--generated-config',type=Path,required=True)
    args=parser.parse_args()
    dest=Path(__file__).resolve().parents[1]/'firmware_assets'; dest.mkdir(exist_ok=True)
    shutil.copyfile(args.firmware,dest/'base.uf2'); shutil.copyfile(args.picotool,dest/'picotool.exe')
    text=args.generated_config.read_text(encoding='utf-8')
    compressed=bytes(int(v,16) for v in re.search(r'#define CONFIGURATION \{([^}]+)\}',text)[1].split(','))
    sha=lambda data:hashlib.sha256(data).hexdigest()
    manifest=dict(version=1,profile='Nuclear Pico - five APA102 frets',
        template_sha256=sha((dest/'base.uf2').read_bytes()),picotool_sha256=sha((dest/'picotool.exe').read_bytes()),
        compatible_config_sha256=[sha(args.original_config.read_bytes()),sha(brotli.decompress(compressed))])
    (dest/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
