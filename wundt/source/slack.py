import json
import re
import os
import glob
from collections import defaultdict

import networkx as nx
import pandas as pd
from pprint import pprint

from wundt.data import get_path


def load_users_and_channels(slack_dir):
    with open(get_path(slack_dir, 'channels.json')) as f:
        data = json.load(f)
        
    with open(get_path(slack_dir, 'users.json')) as f:
        user_data = json.load(f)
    
    users_df = pd.DataFrame.from_dict(user_data)
    channels_df = pd.DataFrame.from_dict(data)
    return users_df, channels_df


def get_channel_directories(slack_dir):
    channel_directories = [x[0] for x in os.walk(slack_dir)][1:]
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

