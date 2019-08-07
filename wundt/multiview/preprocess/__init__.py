from wundt.multiview import datastructures 
import pandas as pd
import numpy as np
from ast import literal_eval
import json
import os
import json
from pydoc import locate
import glob

"""
This module contains various functions to preprocess slack dataset. One of the assumptions in this module is all necessary actions are related to interaction of the users is
inside "People Analytics.xlsx" and "Actions.csv" files. 
Given the above two files this module will produce edge list file and json files for both temporal and static graphs. 
"""

from wundt.multiview.utils.preprocess import display_error, array_softmax, get_topics_from_config, calculate_response_rate_weight, to_json_serializable
from wundt.multiview.utils.preprocess  import MessageCategories, TopicType, MessageWrapper, UsersInfoWrapper


class TemporalGraphsBuilder(object):
    def __init__(self, config):
        self.config = config
    def load_dataset(self):
        """Loads action files and creates temporal graph for each action type.
        """
        print("Loading people analytics messages data")
        messages_df = pd.read_excel(self.config["dataset"]["pa_file_path"], "Message")
        users_df = pd.read_excel(self.config["dataset"]["pa_file_path"], "user")
        print("Loading people analytics reactions data")
        reactions_df = self._load_reaction_data()

        print("Loading users information")
        slack_id2username = {}
        with open(self.config["dataset"]["slack_users_file_path"]) as slack_data_file:
            slack_data = json.load(slack_data_file)
            for d in slack_data:
                slack_id2username[d["id"]] = d["name"]
        
        print("Building users information metadata")
        self.users_info_wrapper = UsersInfoWrapper()
        self.users_info_wrapper.build_from_raw(users_df, reactions_df, slack_id2username)
        
        messages_df = messages_df.sort_values(['channel', 'date_time'], ascending=[True, True])
        messages_df = messages_df.reset_index(drop=True)


        print("Building graphs")
        
        index2topic = {}
        for channel in self.config["topic_types"]:
            index2topic[channel] = {}
            for topic in self.config["topic_types"][channel]:
                index_by_channel = self.config["topic_types"][channel][topic]["index_by_channel"]
                index2topic[channel][index_by_channel] =  topic
        prev_m_wrapper = None
        self.graphs = self._init_graphs()
        for index, row in messages_df.iterrows():
            channel_num_topics = self.config["channels"][row["channel"]]["num_topics"]
            current_m_wrapper = MessageWrapper(self.users_info_wrapper, row, index2topic, channel_num_topics)
            self._add_edges(prev_m_wrapper, current_m_wrapper)
            prev_m_wrapper = current_m_wrapper
        self.slack_id2username = slack_id2username


    def _add_edges(self, prev_m_wrapper, current_m_wrapper):

        source_node = self.users_info_wrapper.get_default_node_name(current_m_wrapper.source_user["hashcode"], self.config)
        target_node = self.users_info_wrapper.get_default_node_name(current_m_wrapper.target_user["hashcode"], self.config)
        timestamp = current_m_wrapper.date_time.timestamp()
        self.graphs["connected"].add_edge((source_node, target_node, timestamp))
        self.graphs["undirected"].add_edge((source_node, target_node, timestamp, 1))
        self.graphs["directed"].add_edge((source_node, target_node, timestamp, 1))
        if current_m_wrapper.message_type == "Direct Mention":
            self.graphs["mention"].add_edge((source_node, target_node, timestamp, 1))
        
        self.graphs["sentiment_directed"].add_edge((source_node, target_node, timestamp, current_m_wrapper.sentiment_weight))
        self.graphs["sentiment_undirected"].add_edge((source_node, target_node, timestamp, current_m_wrapper.sentiment_weight))
        message_categories = current_m_wrapper.message_categories
        message_category_edges = []
        for category in message_categories:
            message_category_edges.append((source_node, target_node, category, timestamp, message_categories[category]))
        self.graphs["message_category"].add_edges(message_category_edges)

        message_topics = current_m_wrapper.message_topics
        message_topics_edges = []
        for topic in message_topics:
            message_topics_edges.append((source_node, target_node, topic, timestamp, message_topics[topic]))
        self.graphs["topic_category"].add_edges(message_topics_edges)

        if prev_m_wrapper is not None:
            prev_message_source_node = self.users_info_wrapper.get_default_node_name(prev_m_wrapper.source_user["hashcode"], self.config)
            current_channel = current_m_wrapper.channel
            prev_channel = prev_m_wrapper.channel
            
            if prev_message_source_node!=source_node and current_channel == prev_channel:
          
                prev_message_timestamp = prev_m_wrapper.date_time.timestamp()

                response_weight = calculate_response_rate_weight(timestamp, prev_message_timestamp, self.config["temporal-graphs"]["response_rate"])

                response_rate_edge = (source_node, prev_message_source_node, timestamp, response_weight)
                self.graphs["response_rate"].add_edge(response_rate_edge)
                reply_edge = (source_node, prev_message_source_node, timestamp, 1)
                self.graphs["reply"].add_edge(reply_edge)


    def _load_reaction_data(self):
        actions_df = pd.read_csv(self.config["dataset"]["actions_file_path"])

        output = {
            "reacted_by": [],
            "source_msg_id": [],
            "channel_id": [],
            "message_owner": [],
            "reaction": [],
            "slack_id":[]
        }

        message_owner = {}

        for index, row in actions_df.iterrows():
            source_node = row["source-actor"]
            source_content = literal_eval(row["source-content"])
            if source_content["type"] == "message":
                message_owner[row["id"]] = source_node
            if source_content["type"] != "reaction":
                continue
            content_type = source_content["type"]
            source_message_id = source_content["parent_id"]
            if content_type == "reaction":
                reaction_type = source_content["subtype"]
                channel_id = source_content["channel_id"]
                reacted_by = source_node

                output["reacted_by"].append(reacted_by)
                output["source_msg_id"].append(source_message_id)
                output["channel_id"].append(channel_id)
                output["message_owner"].append(message_owner[source_message_id])
                output["reaction"].append(reaction_type)
                output["slack_id"].append(source_content["user"])

        output_df = pd.DataFrame(output)
        return output_df


    
                
   
   
    def _init_graphs(self):
        output = {}
        for graph_name in self.config["temporal-graphs"]:
            graph_type = self.config["temporal-graphs"][graph_name]["graph_type"]
            directed = self.config["temporal-graphs"][graph_name]["directed"]

            if graph_type == "temporal_unweighted":
                output[graph_name] = datastructures.TemporalUnweightedGraph(directed=directed)
            elif graph_type == "temporal_weighted":
                weight_type = locate(self.config["temporal-graphs"][graph_name]["weight_type"])
                output[graph_name] = datastructures.TemporalWeightedGraph(directed=directed, weight_is_list=weight_type==list)
                
            elif graph_type == "temporal_multiplex":
                weight_type = locate(self.config["temporal-graphs"][graph_name]["weight_type"])
                relations = self.config["temporal-graphs"][graph_name]["relations"]
                output[graph_name] = datastructures.TemporalMultiplexGraph(directed=directed, weight_is_list=weight_type == list)
        return output
    def include_node_metadata(self, nodes):
        output = []
        for node in nodes:
            node_user = self.users_info_wrapper.get_user_by_index(node)
            node_user["label"] = node_user["username"]
            node_user["id"] = node_user["user_index"]
            output.append(node_user)
        return output
            
            
    def _save_graphs2json(self, output_dir):
        if not os.path.exists(os.path.join(output_dir, "jsons")):
            os.makedirs(os.path.join(output_dir, "jsons"))
        for graph_name in self.graphs:
            network = self.graphs[graph_name].to_visjs_format()
            nodes = self.include_node_metadata(network["nodes"])
            network["nodes"] = nodes
            with open(os.path.join(output_dir, "jsons", graph_name + ".json"), "w+") as output_file:
                json.dump(network, output_file)

    def save_graphs2edgelist(self, output_dir):
        if not os.path.exists(os.path.join(output_dir, "edgelists")):
            os.makedirs(os.path.join(output_dir, "edgelists"))
        for graph_name in self.graphs:
            with open(os.path.join(output_dir, "edgelists", graph_name + ".csv"), "w+") as output_file:
                columns = self.graphs[graph_name].get_column_names()
                header = ",".join(columns)
                output_file.write(header + "\n")
                if self.config["temporal-graphs"][graph_name]["graph_type"] == "temporal_weighted":
                    if self.config["temporal-graphs"][graph_name]["weight_type"] == "list":
                        edges = self.graphs[graph_name].get_edgelist(data=True, sum_weights=False)
                    else:
                        edges = self.graphs[graph_name].get_edgelist(data=True, sum_weights=True)
                        
                else:
                    edges = self.graphs[graph_name].get_edgelist(data=True)
                for edge in edges:
                    output_file.write(",".join(list(map(str,edge)))+"\n")
        
        
    def save_graphs(self):
        print("Saving graphs to disk")
        result_dir = self.config["dataset"]["output_dir"]
        
        if not os.path.exists(result_dir):
            os.makedirs(result_dir)

        if not os.path.exists(os.path.join(result_dir, "graphs")):
            os.makedirs(os.path.join(result_dir, "graphs"))
        
        if not os.path.exists(os.path.join(result_dir, "graphs", "temporal")):
            os.makedirs(os.path.join(result_dir, "graphs", "temporal"))
        formats = self.config["dataset"]["graph_save_format"]

        output_dir = os.path.join(result_dir, "graphs", "temporal")
        if "json" in formats:
            self._save_graphs2json(output_dir)
        if "edgelist" in formats:
            self.save_graphs2edgelist(output_dir)
        self.save_users_meta()
        
        
        
    def save_users_meta(self):
        output_dir = self.config["dataset"]["output_dir"]
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        self.users_info_wrapper.save_metadata(os.path.join(output_dir, "users-matadata.csv"))



class StaticGraphsBuilder(object):
    def __init__(self, config):
        self.config = config
    def load_dataset(self):
        self.graphs = {}

        self.users_info_wrapper = UsersInfoWrapper()
        self.users_info_wrapper.build_from_metadata(os.path.join(self.config["dataset"]["output_dir"], "users-matadata.csv"))

        for graph_name in self.config["static-graphs"]:
            print("Loading %s temporal graph"%graph_name)
            t_graph_edgelist_path = os.path.join(self.config["dataset"]["output_dir"], "graphs", "temporal", "edgelists", graph_name + ".csv")
            t_graph_df = pd.read_csv(t_graph_edgelist_path, sep=",", header=0)
            graph_type = self.config["static-graphs"][graph_name]["graph_type"]
            directed = self.config["static-graphs"][graph_name]["directed"]
            if graph_type == "unweighted":
                self.graphs[graph_name] = datastructures.UnweightedGraph(directed=directed)
            elif graph_type == "weighted":
                weight_type = locate(self.config["static-graphs"][graph_name]["weight_type"])
                self.graphs[graph_name] = datastructures.WeightedGraph(directed=directed, weight_is_list=weight_type==list)
                
            elif graph_type == "multiplex":
                weight_type = locate(self.config["static-graphs"][graph_name]["weight_type"])
                relations = self.config["static-graphs"][graph_name]["relations"]
                self.graphs[graph_name] = datastructures.MultiplexGraph(directed=directed, weight_is_list=weight_type == list)
            print("Building %s static graph"%graph_name)
            for index, row in t_graph_df.iterrows():
                source = int(row["source"])
                target = int(row["target"])
                timestamp = row["timestamp"]
                if graph_type == "unweighted":
                    self.graphs[graph_name].add_edge((source, target))
                elif graph_type == "weighted":
                    weight = row["weight"]
                    if (type(weight) == dict):
                        weight = weight["weight"]
                    self.graphs[graph_name].add_edge((source, target, weight))
                elif graph_type == "multiplex":
                    weight = row["weight"]
                    relation = row["relation"]
                    if (type(weight) == dict):
                        weight = weight["weight"]
                    self.graphs[graph_name].add_edge((source, target, relation, weight))
                else:
                    raise ValueError("Unrecognized graph type:'%s'"%graph_type)

    def include_node_metadata(self, nodes):
        output = []
        for node in nodes:
            node_user = self.users_info_wrapper.get_user_by_index(node)
            node_user["label"] = node_user["username"]
            node_user["id"] = node_user["user_index"]
            output.append(node_user)
        return output
    
    def _save_graphs2json(self, output_dir):
        if not os.path.exists(os.path.join(output_dir, "jsons")):
            os.makedirs(os.path.join(output_dir, "jsons"))
        for graph_name in self.graphs:
            network = self.graphs[graph_name].to_visjs_format()
            nodes = self.include_node_metadata(network["nodes"])
            network["nodes"] = nodes
            with open(os.path.join(output_dir, "jsons", graph_name + ".json"), "w+") as output_file:
                json.dump(network, output_file)

    def save_graphs2edgelist(self, output_dir):
        if not os.path.exists(os.path.join(output_dir, "edgelists")):
            os.makedirs(os.path.join(output_dir, "edgelists"))
        for graph_name in self.graphs:
            with open(os.path.join(output_dir, "edgelists", graph_name + ".csv"), "w+") as output_file:
                columns = self.graphs[graph_name].get_column_names()
                header = ",".join(columns)
                output_file.write(header + "\n")
                if self.config["static-graphs"][graph_name]["graph_type"] == "weighted":
                    if self.config["static-graphs"][graph_name]["weight_type"] == "list":
                        edges = self.graphs[graph_name].get_edgelist(data=True, sum_weights=False)
                    else:
                        edges = self.graphs[graph_name].get_edgelist(data=True, sum_weights=True)
                        
                else:
                    edges = self.graphs[graph_name].get_edgelist(data=True)
                for edge in edges:
                    if type(edge[-1]) == dict:
                        edge = edge[:-1] + (edge[-1]["weight"], )
                    output_file.write(",".join(list(map(str,edge)))+"\n")
        
        
    def save_graphs(self):
        print("Saving graphs to disk")
        result_dir = self.config["dataset"]["output_dir"]
        
        if not os.path.exists(result_dir):
            os.makedirs(result_dir)

        if not os.path.exists(os.path.join(result_dir, "graphs")):
            os.makedirs(os.path.join(result_dir, "graphs"))
        
        if not os.path.exists(os.path.join(result_dir, "graphs", "static")):
            os.makedirs(os.path.join(result_dir, "graphs", "static"))
        formats = self.config["dataset"]["graph_save_format"]

        output_dir = os.path.join(result_dir, "graphs", "static")
        if "json" in formats:
            self._save_graphs2json(output_dir)
        if "edgelist" in formats:
            self.save_graphs2edgelist(output_dir)


class TemporalSnapshotGraphsBuilder(object):
    def __init__(self, config):
        self.config = config
    def load_temporal_graphs(self):
        self.users_info_wrapper = UsersInfoWrapper()
        self.users_info_wrapper.build_from_metadata(os.path.join(self.config["dataset"]["output_dir"], "users-matadata.csv"))

        t_graphs = {}

        t_graphs_info = {}
        
    
        print("Loading temporal graphs")
        for graph_name in self.config["temporal-graphs"]:
            t_graph_edgelist_path = os.path.join(self.config["dataset"]["output_dir"], "graphs", "temporal", "edgelists", graph_name + ".csv")
            t_graph_df = pd.read_csv(t_graph_edgelist_path, sep=",", header=0)
            graph_type = self.config["temporal-graphs"][graph_name]["graph_type"]
            directed = self.config["temporal-graphs"][graph_name]["directed"]

            if graph_type == "temporal_unweighted":
                t_graphs[graph_name] = datastructures.TemporalUnweightedGraph(directed=directed)
            elif graph_type == "temporal_weighted":
                weight_type = locate(self.config["temporal-graphs"][graph_name]["weight_type"])
                t_graphs[graph_name] = datastructures.TemporalWeightedGraph(directed=directed, weight_is_list=weight_type==list)
                
            elif graph_type == "temporal_multiplex":
                weight_type = locate(self.config["temporal-graphs"][graph_name]["weight_type"])
                relations = self.config["temporal-graphs"][graph_name]["relations"]
                t_graphs[graph_name] = datastructures.TemporalMultiplexGraph(directed=directed, weight_is_list=weight_type == list)
            else:
                raise ValueError("Unrecognized graph type:'%s'"%graph_type)
            start_timestamp = np.finfo(np.float64).max
            end_timestamp = 0

            for index, row in t_graph_df.iterrows():
                source = int(row["source"])
                target = int(row["target"])
                timestamp = row["timestamp"]

                if timestamp < start_timestamp:
                    start_timestamp = timestamp
                if timestamp > end_timestamp:
                    end_timestamp = timestamp
                    
                if graph_type == "temporal_unweighted":
                    t_graphs[graph_name].add_edge((source, target, timestamp))
                elif graph_type == "temporal_weighted":
                    weight = row["weight"]
                    if (type(weight) == dict):
                        weight = weight["weight"]
                    t_graphs[graph_name].add_edge((source, target, timestamp, weight))
                elif graph_type == "temporal_multiplex":
                    weight = row["weight"]
                    relation = row["relation"]
                    if (type(weight) == dict):
                        weight = weight["weight"]
                    t_graphs[graph_name].add_edge((source, target, relation, timestamp, weight))
                else:
                    raise ValueError("Unrecognized graph type:'%s'"%graph_type)
            t_graphs_info[graph_name] = {
                "start_timestamp": start_timestamp,
                "end_timestamp":end_timestamp
            }
        return t_graphs, t_graphs_info
    def load_dataset(self):
        t_graphs, t_graphs_info = self.load_temporal_graphs()
        print("Building snapshot graphs")
        self.snapshot_graphs = {}
        self.snapshot_graphs_range = {}
        for graph_name in t_graphs:
            start_timestamp = t_graphs_info[graph_name]["start_timestamp"]
            end_timestamp = t_graphs_info[graph_name]["end_timestamp"]
            snapshot_graphs = []
            steps = self.config["temporal"]["snapshot_length_units"]
            self.snapshot_graphs_range[graph_name] = []
            for ts in range(int(start_timestamp), int(end_timestamp), steps):
                snapshot_graphs.append(t_graphs[graph_name].get_snapshot_graph(ts, ts + steps))
                self.snapshot_graphs_range[graph_name].append({"start":ts, "end":ts+steps})
            self.snapshot_graphs[graph_name] = snapshot_graphs

    def include_node_metadata(self, nodes):
        output = []
        for node in nodes:
            node_user = self.users_info_wrapper.get_user_by_index(node)
            node_user["label"] = node_user["username"]
            node_user["id"] = node_user["user_index"]
            output.append(node_user)
        return output
    def _save_graphs2json(self, output_dir):
        if not os.path.exists(os.path.join(output_dir, "jsons")):
            os.makedirs(os.path.join(output_dir, "jsons"))
        for graph_name in self.snapshot_graphs:
            if not os.path.exists(os.path.join(output_dir, "jsons", graph_name)):
                os.mkdir(os.path.join(output_dir, "jsons", graph_name))
            for i in range(len(self.snapshot_graphs[graph_name])):
                
                network = self.snapshot_graphs[graph_name][i].to_visjs_format()
                nodes = self.include_node_metadata(network["nodes"])
                network["nodes"] = nodes
                with open(os.path.join(output_dir, "jsons", graph_name, "snapshot-%d"%i + ".json"), "w+") as output_file:
                    json.dump(network, output_file)

    def save_graphs2edgelist(self, output_dir):
        if not os.path.exists(os.path.join(output_dir, "edgelists")):
            os.makedirs(os.path.join(output_dir, "edgelists"))
        for graph_name in self.snapshot_graphs:
            if not os.path.exists(os.path.join(output_dir, "edgelists", graph_name)):
                os.mkdir(os.path.join(output_dir, "edgelists", graph_name))
            for i in range(len(self.snapshot_graphs[graph_name])):
                current_snapshot = self.snapshot_graphs[graph_name][i]

                with open(os.path.join(output_dir, "edgelists", graph_name, "snapshot-%d"%i + ".csv"), "w+") as output_file:
                    columns = current_snapshot.get_column_names()
                    header = ",".join(columns)
                    output_file.write(header + "\n")
                    edges = current_snapshot.get_edges(data=True)
                    for edge in edges:
                        output_file.write(",".join(list(map(str,edge)))+"\n")
        
        
    def save_graphs(self):
        print("Saving graphs to disk")
        result_dir = self.config["dataset"]["output_dir"]
        
        if not os.path.exists(result_dir):
            os.makedirs(result_dir)

        if not os.path.exists(os.path.join(result_dir, "graphs")):
            os.makedirs(os.path.join(result_dir, "graphs"))
        
        if not os.path.exists(os.path.join(result_dir, "graphs", "snapshots")):
            os.makedirs(os.path.join(result_dir, "graphs", "snapshots"))
        formats = self.config["dataset"]["graph_save_format"]

        output_dir = os.path.join(result_dir, "graphs", "snapshots")
        if "json" in formats:
            self._save_graphs2json(output_dir)
        if "edgelist" in formats:
            self.save_graphs2edgelist(output_dir)
        if not os.path.exists(os.path.join(result_dir, "graphs", "snapshot-graphs-range")):
            os.mkdir(os.path.join(result_dir, "graphs", "snapshot-graphs-range"))
        for graph_name in self.snapshot_graphs_range:
            output_json = {}
            with open(os.path.join(result_dir, "graphs", "snapshot-graphs-range", graph_name+".csv"), "w+") as range_file:
                range_file.write("snapshot_index,start,end\n")
                for r in range(len(self.snapshot_graphs_range[graph_name])):
                    range_info = self.snapshot_graphs_range[graph_name][r];
                    range_file.write(str(r) + "," + str(range_info["start"]) + "," + str(range_info["end"]) + "\n")
                    output_json[r] = range_info
 
            with open(os.path.join(result_dir, "graphs", "snapshot-graphs-range", graph_name+".json"), "w+") as range_json_file:
                json.dump(output_json, range_json_file)
                    


class TemporalDynamicGraphBuilder(TemporalSnapshotGraphsBuilder):
    def __init__(self, config):
        self.config = config
    def load_dataset(self):
        t_graphs, t_graphs_info = self.load_temporal_graphs()
        print("Building snapshot graphs")
        self.snapshot_graphs = {}
        self.snapshot_graphs_range = {}
        for graph_name in t_graphs:
            start_timestamp = t_graphs_info[graph_name]["start_timestamp"]
            end_timestamp = t_graphs_info[graph_name]["end_timestamp"]
            current_snapshot_graphs = []
            steps = self.config["temporal"]["snapshot_length_units"]
            self.snapshot_graphs_range[graph_name] = []
            for ts in range(int(start_timestamp), int(end_timestamp), steps):
                current_snapshot_graphs.append(t_graphs[graph_name].get_evolution_snapshot_graph(ts + steps))
                self.snapshot_graphs_range[graph_name].append({"timestamp":ts+steps})
            self.snapshot_graphs[graph_name] = current_snapshot_graphs
    def save_graphs(self):
        print("Saving graphs to disk")
        result_dir = self.config["dataset"]["output_dir"]
        
        if not os.path.exists(result_dir):
            os.makedirs(result_dir)

        if not os.path.exists(os.path.join(result_dir, "graphs")):
            os.makedirs(os.path.join(result_dir, "graphs"))
        
        if not os.path.exists(os.path.join(result_dir, "graphs", "dynamic-snapshots")):
            os.makedirs(os.path.join(result_dir, "graphs", "dynamic-snapshots"))
        formats = self.config["dataset"]["graph_save_format"]

        output_dir = os.path.join(result_dir, "graphs", "dynamic-snapshots")
        if "json" in formats:
            self._save_graphs2json(output_dir)
        if "edgelist" in formats:
            self.save_graphs2edgelist(output_dir)
        if not os.path.exists(os.path.join(result_dir, "graphs", "dynamic-snapshot-graphs-range")):
            os.mkdir(os.path.join(result_dir, "graphs", "dynamic-snapshot-graphs-range"))
        for graph_name in self.snapshot_graphs_range:
            output_json = {}
            with open(os.path.join(result_dir, "graphs", "dynamic-snapshot-graphs-range", graph_name+".csv"), "w+") as range_file:
                range_file.write("snapshot_index,timestamp\n")
                for r in range(len(self.snapshot_graphs_range[graph_name])):
                    range_info = self.snapshot_graphs_range[graph_name][r];
                    range_file.write(str(r) + "," + str(range_info["timestamp"]) + "\n")
                    output_json[r] = range_info
 
            with open(os.path.join(result_dir, "graphs", "dynamic-snapshot-graphs-range", graph_name+".json"), "w+") as range_json_file:
                json.dump(output_json, range_json_file)