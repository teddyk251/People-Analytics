import json
import os
import glob
from collections import defaultdict

import networkx as nx
import pandas as pd
from pprint import pprint

SLACK_FILE_DIR = 'data/iCog Slack export Apr 27 2015 - Sep 3 2018'

def get_path(fn):
    return os.path.join(SLACK_FILE_DIR, fn)

def load_users_and_channels():
    with open(get_path('channels.json')) as f:
        data = json.load(f)
        
    with open(get_path('users.json')) as f:
        user_data = json.load(f)
    
    users_df = pd.DataFrame.from_dict(user_data)
    channels_df = pd.DataFrame.from_dict(data)
    return users_df, channels_df

def get_channel_directories():
    channel_directories = [x[0] for x in os.walk(SLACK_FILE_DIR)][1:]
    return channel_directories

def scan_msg_types(channel_directories, channels_df):
    msg_types = defaultdict(set)
    msg_example = defaultdict(dict)

    msg_keys = defaultdict(int)
    messages = []

    for path in channel_directories:
        channel_name = os.path.basename(path)
        files = glob.glob(path + '/*.json')
        channel_info = channels_df.loc[channels_df['name'] == channel_name]
        channel_id = channel_info.id.values[0]
        print(channel_id, channel_name)
        for fn in files:
            msg_date = fn[-15:-5]

            with open(fn) as f:
                msg_data = json.load(f)
                
            for msg in msg_data:
                for k in msg:
                    msg_keys[k] += 1
                msg_type = msg['type']
                msg_subtype = msg.get('subtype', 'chat')
                msg_types[msg_type].add(msg_subtype)
                if msg_subtype not in msg_example[msg_type]:
                    msg_example[msg_type][msg_subtype] = msg
                idx = len(messages)
                messages.append({
                    'id':idx,
                    'type':msg_type,
                    'subtype':msg_subtype,
                    'ts': pd.Timestamp(float(msg['ts']),unit='s'),
                    'channel_id': channel_id,
                    'channel_name': channel_name,
                    'text': msg.get('text', None),
                    'user': msg.get('user', None)
                })
                if 'reactions' in msg:
                    for reaction in msg['reactions']:
                        for user in reaction['users']:
                            reaction_idx = len(messages)
                            messages.append({
                                'id': reaction_idx,
                                'parent_id': idx,
                                'type': 'reaction',
                                'subtype': reaction['name'],
                                'user': user,
                                'ts': pd.Timestamp(float(msg['ts']),unit='s'),
                                'channel_id': channel_id,
                                'channel_name': channel_name,
                            })
                #print(msg)
    return msg_keys, msg_types, msg_example, messages

import re
def parse_file_comment_text(text):
    from_user = None
    to_user = None
    comment = None
    m = re.match(r"<@(U\w+)> commented on <@(U\w+)>.s file <.+\|.+>:(.*)$", eg)
    if m:
        from_user = m[1]
        to_user = m[2]
        comment = m[3]

    return from_user, to_user, comment

def build_action_graph(messages, users_df, channels_df):
    G=nx.DiGraph()
    G.add_nodes_from(users_df.id)
    G.add_nodes_from(channels_df.id)
    default_subtypes = ['chat', 'reply_broadcast', 'thread_broadcast', 'channel_join', 'channel_name', 'channel_purpose', 'channel_topic', 'channel_archive', 'channel_unarchive', 'pinned_item', 'channel_leave']
    for m in messages:
        if 'bot' in m['subtype']:
            # bots are not people
            pass
        elif m['user'] and m['channel_id']:
            if m['type'] != 'reaction' and m['subtype'] not in default_subtypes:
                print("not a chat: ", m)
            m = dict(m)
            G.add_edge(m['user'], m['channel_id'], attr_dict=m)
        elif m['subtype'] == 'file_comment':
            # should this also add an edge to the channel?
            a,b,c = parse_file_comment_text(m['text'])
            if a:
                m = dict(m)
                m['text'] = c
                G.add_edge(a, b, attr_dict={'text': c})
        else:
            print(m)
            input()
    return G

def collapse_sentiment(period='monthly'):
    pass

if __name__ == "__main__":
    users_df, channels_df = load_users_and_channels()
    channel_directories = get_channel_directories()
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