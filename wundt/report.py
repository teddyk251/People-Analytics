# -*- coding: utf-8 -*-
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pprint import pprint
import pandas as pd
import matplotlib.pyplot as plt

from wundt.source.slack import *
from wundt.graph import build_action_graph


def do_report(data_directories):
    # TODO: # Eventually this should automatically inspect the available data and source modules.
    # But for now we just hard code it
    for directory in data_directories:
        if directory == "slack":
            print("Importing slack data")
            slack_directories = [os.path.join(directory, item) for item in os.listdir(directory) if os.path.isdir(os.path.join(directory, item))]
            print("Found slack directories", slack_directories)
            if len(slack_directories) > 1:
                print("Multiple slack dirs in path, work needed to handle this...")
                return
            SLACK_FILE_DIR = slack_directories[0]

            users_df, channels_df, m_df = import_slack_archive(SLACK_FILE_DIR, dump_info=False)

            print(users_df.loc[:, users_df.columns.isin(['name', 'id'])])

            print(m_df)
            print(m_df.describe())
            print(m_df.subtype.value_counts())

            G = build_action_graph(m_df, users_df, channels_df)
            print("Graph built")
            print(G)
            print(G.number_of_nodes(), G.number_of_edges())
        if directory == "gitlab":
            print("Importing gitlab data")
            print("TODO: Implement me!")


    # The visualisations are not very helpful at the moment
    #graph_visuals(G)


def graph_visuals(G):
    nx.draw_spring(G)
    plt.savefig("path.png")
    plt.clf()
    nx.draw_random(G)
    plt.savefig("pathr.png")
    plt.clf()
    nx.draw_circular(G)
    plt.savefig("pathc.png")
    plt.clf()
    nx.draw_spectral(G)
    plt.savefig("paths.png")
    plt.clf()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=str, default="data/iCog")
    args = parser.parse_args()

    data_directories = [os.path.join(args.path, item) for item in os.listdir(args.path) if os.path.isdir(os.path.join(args.path, item))]
    print("Found data directories", data_directories)
    do_report(data_directories)
