import re
import networkx as nx


def build_action_graph(messages, users_df, channels_df):
    G=nx.DiGraph()
    G.add_nodes_from(users_df.id)
    G.add_nodes_from(channels_df.id)
    default_subtypes = ['chat', 'reply_broadcast', 'thread_broadcast', 'channel_join', 'channel_name', 'channel_purpose', 'channel_topic', 'channel_archive', 'channel_unarchive', 'pinned_item', 'channel_leave']
    for m in messages.itertuples():
        if 'bot' in m.subtype:
            # bots are not people
            pass
        elif m.user and m.channel_id:
            if m.type != 'reaction' and m.subtype not in default_subtypes:
                print("not a chat: ", m)
            G.add_edge(m.user, m.channel_id, attr_dict=dict(m._asdict()))
        elif m.subtype == 'file_comment':
            # should this also add an edge to the channel?
            G.add_edge(m.user, m.target, attr_dict=dict(m._asdict()))
        else:
            print(m)
            input()
    return G

def collapse_sentiment(period='monthly'):
    pass
