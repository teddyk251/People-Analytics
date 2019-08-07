from collections import defaultdict
import numpy as np
import pandas as pd
import yaml


def to_regular_dict(d):
    return to_regular_dict_helper(d)
def to_regular_dict_helper(d):
    if isinstance(d, defaultdict):
        d = {key: to_regular_dict_helper(value) for key, value in d.items()}
    return d
def to_json_serializable(d):
    if isinstance(d, defaultdict):
        d = {key: to_json_serializable(value) for key, value in d.items()}
    elif isinstance(d, set):
        d = list(d)
    return d

def calculate_response_rate_weight(message_timestamp, prev_message_timestamp, config):
    time_unit = config["time_unit"]
    assert time_unit in ["minute", "second", "hour", "day"], "Time unit of the response rate graph configuration should be one of:- (second, minute, hour, day)"
    a = config["a"]
    b = config["b"]
    interval_in_seconds = message_timestamp - prev_message_timestamp
    
    if time_unit == "minute":
        denominator = 60.0
    elif time_unit == "hour":
        denominator = 60.0 * 60.0
    elif time_unit == "day":
        denominator = 24 * 60.0 * 60.0
    else:
        denominator = 1.0
    inteval_converted = interval_in_seconds / denominator
    
    if (b * inteval_converted + a)> 700: # avoids overflow
        return 0;
    return 1.0 / (1.0 + np.exp(a + b * inteval_converted))
    
def display_error(message):
    print("\x1B[31;40m" + message + "\x1B[0m")

def array_softmax(array):
    return np.exp(array - np.max(array)) / np.sum(np.exp(array - np.max(array)))

def get_topics_from_config(config):
    topics = []
    channels_num_topics = {}
    for channel in config["channels"]:
        channels_num_topics[channel] = config["channels"][channel]["num_topics"]
        for topic in config["topic_types"][channel]:
            topics.append(
                {
                    "name": topic,
                    "short_name": config["topic_types"][channel][topic]["short_name"],
                    "index_by_channel": config["topic_types"][channel][topic]["index_by_channel"],
                    "index": config["topic_types"][channel][topic]["topic_index"],
                    "channel":channel
                }
            )
    return topics, channels_num_topics


class MessageCategories(object):
    categories_cols = ["categorization_1", "categorization_2", "categorization_3", "categorization_4", "categorization_5", "categorization_6"]
    
    categories_weights = array_softmax(np.arange(len(categories_cols)-1, -1, -1)).tolist()
    def __init__(self, row):
        self.built = False
        self._build(row)
    def _build(self, row):
        self.message_categories = {}
        for i in range(len(MessageCategories.categories_cols)):
            col = MessageCategories.categories_cols[i]
            col_weight = MessageCategories.categories_weights[i]
            current_col_category = row[col]
            self.message_categories[current_col_category] = col_weight
        self.built = True
class TopicType(object):
    topics_cols = ["topic_1", "topic_2", "topic_3", "topic_4", "topic_5"]
    def __init__(self, row,index2topic, channel_num_topics):
        self.built = False
        self._build(row,index2topic,  channel_num_topics)

    def get_topic_cols_weights(self, channel_num_topics):
        weights = array_softmax(np.arange(channel_num_topics-1, -1, -1))
        return weights
    def _build(self, row, index2topic, channel_num_topics):
        self.message_topics = {}
        topic_cols_weights = self.get_topic_cols_weights(channel_num_topics)
        channel = row["channel"]
        for i in range(channel_num_topics):
            col = TopicType.topics_cols[i]
            col_weight = topic_cols_weights[i]
            topic_index = row[col]
            topic = index2topic[channel][topic_index]
            self.message_topics[topic] = col_weight
        self.build = True

class MessageWrapper(object):
    def __init__(self, users_info_wrapper, row, index2topic, channel_num_topics):
        self.users_info_wrapper = users_info_wrapper
        self._build(row, index2topic, channel_num_topics)
    def _build(self, row, index2topic, channel_num_topics):
        self.source_user = self.users_info_wrapper.get_user_by_hashcode(row["from_node"])
        self.target_user = self.users_info_wrapper.get_user_by_hashcode(row["to_node"])
        self.message_type = row["message_type"]
        self.message_id = row["msg_id"]
        self.channel = row["channel"]
        self.date_time = row["date_time"]
        self.message_categories = MessageCategories(row).message_categories
        self.sentiment_weight = row["Sentiment"]
        self.message_topics = TopicType(row, index2topic, channel_num_topics).message_topics
        self.message_content = row["message"]
    def __str__(self):
        return str(
            "source:'" +str( self.source_user) + "'" +\
            "target:'" + str(self.target_user )+ "'" +\
            "message_id:'" +str( self.message_id )+ "'" +\
            "message_type:'" +str( self.message_type) + "'" +\
            "sentiment_weight:'" + str(self.sentiment_weight) + "'"
            )

class UsersInfoWrapper(object):
    def build_from_metadata(self, metadata_path):
        meta_df = pd.read_csv(metadata_path)

        self.hashSource = {}
        self.hash2username = {}
        self.hash2fakename = {}
        self.hash2index = {}

        for index, row in meta_df.iterrows():
            hashcode = row["hashcode"]
            username = row["username"]
            user_index = row["user_index"]
            fake_name = row["fake_name"]
            hash_source = row["source"]

            self.hashSource[row["hashcode"]] = hash_source
            self.hash2username[hashcode] = username
            self.hash2fakename[hashcode] = fake_name
            self.hash2index[hashcode] = user_index

        self.pa_username2hash = {value: key for key, value in self.hash2username.items() if self.hashSource[key] == "pa"}
        self.pa_fakename2hash = {value: key for key, value in self.hash2fakename.items() if self.hashSource[key] == "pa"}

        self.action_username2hash = {value: key for key, value in self.hash2username.items() if self.hashSource[key] == "action"}
        self.action_fakename2hash = {value: key for key, value in self.hash2fakename.items() if self.hashSource[key] == "action"}
        
        self.index2hash = {value:key for key, value in self.hash2index.items()}
    def get_default_node_name(self, hashcode, config):
        default_node_name = config["users"]["default"]["node_name"]
        if default_node_name == "hashcode":
            return hashcode
        elif default_node_name in ["user_index", "username"]:
            user_info = self.get_user_by_hashcode(hashcode)
            return user_info[default_node_name]
        else:
            ValueError("Node name should be one of: user_index, username and hashcode")
        

    def save_metadata(self, path):
        output = {
            "hashcode": [],
            "username": [],
            "fake_name": [],
            "user_index": [],
            "source":[]
        }
        for hashcode, user_index in self.hash2index.items():
            username = self.hash2username[hashcode]
            fake_name = self.hash2fakename[hashcode]
            hashsource = self.hashSource[hashcode]

            output["hashcode"].append(hashcode)
            output["username"].append(username)
            output["fake_name"].append(fake_name)
            output["user_index"].append(user_index)
            output["source"].append(hashsource)
        output_df = pd.DataFrame(output)
        output_df.to_csv(path)

    def build_from_raw(self, users_df, reactions_df, slack_id2username):
        hashInfo = {}
        hashsource = {}
        for index, row in users_df.iterrows():
            hashInfo[row["user_hashcode"]] = {"real_name":row["real_name"], "fake_name":row["label_name"]}
            hashsource[row["user_hashcode"]] = "pa"
        
        for index, row in reactions_df.iterrows():
            slack_id = row["slack_id"]
            if slack_id == None or slack_id == "None"  or slack_id == "":
                continue
            if row["reacted_by"] not in hashInfo:
                hashInfo[row["reacted_by"]] = {"real_name":slack_id2username[slack_id], "fake_name":None}
                hashsource[row["reacted_by"]] = "action"
            

        self.hashSource = hashsource



        self.hash2username =  {hashcode: info["real_name"] for hashcode, info in hashInfo.items()}
        
        self.hash2fakename =  {hashcode: info["fake_name"] for hashcode, info in hashInfo.items()}
    
        hashecodes = list(hashInfo.keys())
        self.hash2index = {hashcode: i for i, hashcode in enumerate(hashecodes)}        

        self.pa_username2hash = {value: key for key, value in self.hash2username.items() if hashsource[key] == "pa"}
        self.pa_fakename2hash = {value: key for key, value in self.hash2fakename.items() if hashsource[key] == "pa"}

        self.action_username2hash = {value: key for key, value in self.hash2username.items() if hashsource[key] == "action"}
        self.action_fakename2hash = {value: key for key, value in self.hash2fakename.items() if hashsource[key] == "action"}

        self.index2hash = {value:key for key, value in self.hash2index.items()}
        

    def get_user_by_username(self, username, source):
        if source == "pa":
            hashcode = self.pa_username2hash[username]
        elif source == "action":
            hashcode = self.action_username2hash[username]
            
        else:
            raise ValueError("Source should be either:'pa' or 'action', found: %s" % source)
        return {
                "hashcode": hashcode,
                "fake_name": self.hash2fakename[hashcode],
                "username": username,
                "user_index":self.hash2index[hashcode]
            }

    def get_user_by_hashcode(self, hashcode):
        if not hashcode in self.hash2index:
            raise ValueError("Couldn't find hash code: %s"%hashcode)
        return {
                "hashcode": hashcode,
                "fake_name": self.hash2fakename[hashcode],
                "username": self.hash2username[hashcode],
                "user_index":self.hash2index[hashcode]
            }

    def get_user_by_index(self, user_index):
        if not user_index in self.index2hash:
            raise ValueError("Couldn't find user index: %s"%user_index)
        hashcode = self.index2hash[user_index]
        
        return {
                "hashcode": hashcode,
                "fake_name": self.hash2fakename[hashcode],
                "username": self.hash2username[hashcode],
                "user_index":self.hash2index[hashcode]
            }
    
def load_config(config_path):
    with open(config_path) as config_file:
        return yaml.load(config_file, Loader=yaml.FullLoader)