import argparse
from wundt.multiview.utils.preprocess import load_config
from . import TemporalSnapshotGraphsBuilder



"""Generates snapshots of temporal graphs within specified range.
"""


def main(args):
    config = load_config(args.config)
    s_graph_builder = TemporalSnapshotGraphsBuilder(config)
    s_graph_builder.load_dataset()
    s_graph_builder.save_graphs()
    
if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config',default='wundt/multiview/preprocess/config.yml')
    args = parser.parse_args()
    main(args)