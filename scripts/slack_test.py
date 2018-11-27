# -*- coding: utf-8 -*-
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pprint import pprint
import pandas as pd

from wundt.source.slack import *
from wundt.graph import build_action_graph, parse_file_comment_text


SLACK_FILE_DIR = 'data/iCog Slack export Apr 27 2015 - Sep 3 2018'


if __name__ == "__main__":
    users_df, channels_df = load_users_and_channels(SLACK_FILE_DIR)
    channel_directories = get_channel_directories(SLACK_FILE_DIR)
    msg_keys, msg_types, msg_example, messages = scan_msg_types(channel_directories, channels_df)

    m_df = pd.DataFrame(messages)
    print(m_df)
    print(m_df.describe())
    print(m_df.subtype.value_counts())
    #https://raw.githubusercontent.com/iamcal/emoji-data/master/emoji_pretty.json

    pprint(msg_types)
    #pprint(msg_example)
    print(msg_keys)

    eg = '<@U04K91T8E> commented on <@U6NA3UM5L>’s file <https://icog.slack.com/files/U6NA3UM5L/F9CF5EZTL/5a86f8992ae73d3fc20c8bf8.scm|5a86f8992ae73d3fc20c8bf8.scm>: so it looks like 1) we want to use a unique name indicating the particular analysis of the particular moses input file for the "temp_file _xyz" string like"oovc_run1_fold5:model_12"'

    print(parse_file_comment_text(eg))
    G = build_action_graph(messages, users_df, channels_df)
    print("Graph built")
    print(G)
    print(G.number_of_nodes(), G.number_of_edges())
    import matplotlib.pyplot as plt
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