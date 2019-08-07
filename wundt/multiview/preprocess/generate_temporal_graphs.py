import argparse
from wundt.multiview.utils.preprocess import load_config
from . import TemporalGraphsBuilder

"""
This module will create temporal graphs from "People Analytics.xlsx" and "Actions.csv" files. 
The temporal graphs are graphs with edges label with time stamp(timestamp is crossponds to timestamp of interaction).
"""


def main(args):
    config = load_config(args.config)
    t_graph_builder = TemporalGraphsBuilder(config)
    t_graph_builder.load_dataset()
    t_graph_builder.save_graphs()
    
if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config',default='wundt/multiview/preprocess/config.yml')
    args = parser.parse_args()
    main(args)