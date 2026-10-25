"""Grade one local source against a local manifest, printing only aggregate results."""
import argparse,json
from dataclasses import asdict
from pathlib import Path
from .runners.container import DockerJudge,TestCase,InfrastructureError
from .limits import Limits

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--language',choices=['c','cpp','java'],required=True);p.add_argument('--manifest',required=True)
    a=p.parse_args();manifest=Path(a.manifest).resolve();config=json.loads(manifest.read_text(encoding='utf-8'))
    def read(name):
        path=(manifest.parent/name).resolve()
        if not path.is_relative_to(manifest.parent):raise ValueError('Manifest paths must stay within its directory')
        return path.read_bytes()
    cases=[TestCase(read(t['input']),read(t['expected']),t.get('points',1)) for t in config['tests']]
    result=DockerJudge().grade(Path(a.source).read_text(encoding='utf-8'),a.language,cases,
        limits=Limits(config.get('time_limit_ms',2000),config.get('memory_limit_mib',256)),
        io_mode=config.get('io_mode','stdio'),input_filename=config.get('input_filename','input.txt'),output_filename=config.get('output_filename','output.txt'),comparator=config.get('comparator','exact'))
    print(json.dumps(asdict(result),ensure_ascii=False))
if __name__=='__main__':main()
