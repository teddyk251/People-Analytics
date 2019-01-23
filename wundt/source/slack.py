import numpy as np
import json
import re
import os
import glob
from collections import defaultdict

import networkx as nx
import pandas as pd
import hashlib
from pprint import pprint

from wundt.actors import ActorDetails, COLUMN_ROLE as C, create_hash_id_column, D, find_values

def get_path(slack_dir, fn):
    return os.path.join(slack_dir, fn)


def load_users(slack_dir):
    with open(get_path(slack_dir, 'users.json')) as f:
        user_data = json.load(f)
    
    return pd.DataFrame.from_dict(user_data)


def load_channels(slack_dir):
    with open(get_path(slack_dir, 'channels.json')) as f:
        data = json.load(f)
        
    return pd.DataFrame.from_dict(data)


def get_channel_directories(slack_dir):
    channel_directories = [x[0] for x in os.walk(slack_dir)][1:]
    return channel_directories


def scan_message(msg, msg_keys, msg_types, msg_examples):
    for k in msg:
        msg_keys[k] += 1

    msg_type = msg['type']
    msg_subtype = msg.get('subtype', 'chat')
    
    msg_types[msg_type].add(msg_subtype)
    if msg_subtype not in msg_examples[msg_type]:
        msg_examples[msg_type][msg_subtype] = msg


def parse_message(msg, channel_id, channel_name, idx):
    actions = []

    msg_type = msg['type']
    msg_subtype = msg.get('subtype', 'chat')

    actions.append({
        'id': idx,
        'source-type': 'slack',
        'source-content': {
            'type': msg_type,
            'subtype': msg_subtype,
            'channel_id': channel_id,
            'channel_name': channel_name,
            'text': msg.get('text', None),
            'user': msg.get('user', None)
        },
        'ts': pd.Timestamp(float(msg['ts']),unit='s'),
        'source-actor': msg.get('user', None),
        'source-targets': [channel_id],
    })
    if 'reactions' in msg:
        reaction_idx = idx
        for reaction in msg['reactions']:
            for user in reaction['users']:
                reaction_idx += 1
                actions.append({
                    'id': idx,
                    'source-type': 'slack',
                    'source-content': {
                        'parent_id': idx,
                        'type': 'reaction',
                        'subtype': reaction['name'],
                        'channel_id': channel_id,
                        'channel_name': channel_name,
                        'user': user
                    },
                    'ts': pd.Timestamp(float(msg['ts']),unit='s'),
                    'source-actor': user,
                    'source-targets': [channel_id, msg.get('user')],
                })
    return actions


def load_messages(slack_dir, channels_df):
    channel_directories = get_channel_directories(slack_dir)

    msg_types = defaultdict(set)
    msg_examples = defaultdict(dict)
    msg_keys = defaultdict(int)
    messages = []

    for path in channel_directories:
        channel_name = os.path.basename(path)
        files = glob.glob(path + '/*.json')
        channel_info = channels_df.loc[channels_df['name'] == channel_name]
        channel_id = channel_info.id.values[0]
        for fn in files:
            msg_date = fn[-15:-5]

            with open(fn) as f:
                msg_data = json.load(f)
                
            for msg in msg_data:
                idx = len(messages)
                scan_message(msg, msg_keys, msg_types, msg_examples)
                messages.extend(parse_message(msg, channel_id, channel_name, idx))

    return msg_keys, msg_types, msg_examples, messages


def parse_file_comment_text(text):
    """
    >>> parse_file_comment_text('<@U04K91T8E> commented on <@U6NA3UM5L>’s file <https://icog.slack.com/files/U6NA3UM5L/F9CF5EZTL/5a86f8992ae73d3fc20c8bf8.scm|5a86f8992ae73d3fc20c8bf8.scm>: so it looks like 1) we want to use a unique name "oovc_run1_fold5:model_12"')
    ('U04K91T8E', 'U6NA3UM5L', ' so it looks like 1) we want to use a unique name "oovc_run1_fold5:model_12"')
    """
    from_user = None
    to_user = None
    comment = None
    m = re.match(r"<@(U\w+)> commented on <@(U\w+)>.s file <(.+)\|.+>:(.*)", text)
    if m:
        from_user = m[1]
        to_user = m[2]
        file_url = m[3]
        comment = m[4]

    return from_user, to_user, file_url, comment


def parse_file_comment(msg):
    if msg['source-content']['subtype'] == 'file_comment':
        from_user, to_user, file_url, comment = parse_file_comment_text(msg['source-content']['text'])
        msg['source-content']['user'] = from_user 
        msg['source-content']['text'] = comment 

        msg['source-targets'].extend([to_user, file_url]) 


def emoji_convert(msg):
    """ Add the unicode emoji from long name """
    #https://raw.githubusercontent.com/iamcal/emoji-data/master/emoji_pretty.json
    # TODO
    pass


def temporal_targets(messages):
    """ Determine secondary targets from conversation """
    # TODO
    pass


def import_slack_archive(slack_dir, dump_info=False):
    # Load users and channels, there are both "entities" that messages can target
    # (though new entities can be found through the messages themselves, e.g. files and shared links)
    col_names =  ['id', 'name', 'real_name']
    actors_df = load_users(slack_dir)
    #canon_df[i] = [hashlib.sha512(str.encode(str(j))).hexdigest() for j in canon_df[i]]
    #for idx, row in actors_df.iterrows():
    actors_df = create_hash_id_column(col_names, actors_df)       
    
    print("ACTOR_DF_TYPE: ", type(actors_df))
    print(actors_df.iloc[0])
    actors_df.to_csv("reports/users.csv", sep='\t', encoding='utf-8')
    actor_details = ActorDetails('slack', actors_df,
        [C.IGNORE, C.IGNORE, C.SOURCE_ID, C.IGNORE, C.IGNORE, C.IGNORE, C.IGNORE, C.IGNORE, C.IGNORE, C.IGNORE,
        C.USERNAME,
        C.IGNORE,
        #C.ID,
        C.FULL_NAME,
        C.IGNORE,
        C.IGNORE,
        C.IGNORE,
        C.IGNORE,
        C.IGNORE,
        ]
        )
    actor_details.df.to_csv("reports/details.csv", sep='\t', encoding='utf-8')
    channels_df = load_channels(slack_dir)
    
    # Now load in the messages
    msg_keys, msg_types, msg_example, messages = load_messages(slack_dir, channels_df)
    print("msg_keys:::: ", msg_keys)
    #msg_keys.df.to_csv("reports/msg_keys.csv", sep='\t', encoding='utf-8')
    print("Number of slack actions loaded", len(messages))

    f = open('reports/messages.txt', 'w')
    f.write("START: ")
    f.write(str(msg_example))
    # f.write("EXAMPLES: ")
    # f.write(str(msg_example))
    # f.write("MESSAGES: ")
    # f.write(str(messages))
    # f.write("ALEQE")
    f.close()

    # Optionally show some summary of what we found in the raw messages
    if dump_info:
        print("msg_types")
        pprint(msg_types)
        print("msg_example")
        pprint(msg_example)
        print("msg key counts")
        pprint(msg_keys)

    # Apply these functions to each message
    per_message_augmentors = [emoji_convert, parse_file_comment]

    # Apply these functions to the the whole dataset (they still update individual messages,
    # but use messages with neighbouring context)
    all_message_augmentors = [temporal_targets]

    for ma in per_message_augmentors:
        for msg in messages:
            ma(msg)

    for ma in all_message_augmentors:
        ma(messages)

    actions_df = pd.DataFrame(messages)

    col_names = ["source-actor"]

    #actors_df = create_hash_id_column(col_names, actors_df)  

    actions_df = find_values(col_names, actions_df)

    actions_df.to_csv("reports/slack_act.csv", sep='\t', encoding='utf-8')

    return actions_df, actor_details, channels_df