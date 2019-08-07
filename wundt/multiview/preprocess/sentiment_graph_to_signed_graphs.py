import argparse
from wundt.multiview.utils.preprocess import load_config
import os
import pandas as pd
from wundt.multiview import datastructures

"""
Sentiment graphs are signed graphs(edge have sign). This module will split sentiment graphs into three separate graphs, namely neutral, positive and negative sentiment graphs
"""


def save_temporal_graph(output_path, edgelist, weighted):

    with open(output_path, "w+") as output_file:
        if weighted:
            output_file.write("source,target,timestamp,weight\n")
        else:
            output_file.write("source,target,timestamp\n")
        for edge in edgelist:
            output_file.write(",".join(map(str, edge)) + "\n")

def main(args):
    threshold = 0.1
    config = load_config(args.config)
    temporal_graphs_path = os.path.join(config["dataset"]["output_dir"], "graphs", "temporal", "edgelists")
    sentiment_directed_graph_path = os.path.join(temporal_graphs_path, "sentiment_directed.csv")
    sentiment_undirected_graph_path = os.path.join(temporal_graphs_path, "sentiment_undirected.csv")

    directed_df = pd.read_csv(sentiment_directed_graph_path, header=0)
    undirected_df = pd.read_csv(sentiment_undirected_graph_path, header=0)
    
    directed_pos_graph = datastructures.TemporalWeightedGraph(directed=True, weight_is_list=False)
    directed_neg_graph = datastructures.TemporalWeightedGraph(directed=True, weight_is_list=False)
    directed_neut_graph = datastructures.TemporalUnweightedGraph(directed=True)
    
    
    undirected_pos_graph = datastructures.TemporalWeightedGraph(directed=False, weight_is_list=False)
    undirected_neg_graph = datastructures.TemporalWeightedGraph(directed=False, weight_is_list=False)
    undirected_neut_graph = datastructures.TemporalUnweightedGraph(directed=False)

    for index, row in directed_df.iterrows():
        if( - threshold) <= row["weight"] <= threshold:
            directed_neut_graph.add_edge((int(row["source"]), int(row["target"]), row["timestamp"]))
        elif row["weight"] > threshold:
            directed_pos_graph.add_edge((int(row["source"]), int(row["target"]), row["timestamp"], row["weight"]))
        else:
            directed_neg_graph.add_edge((int(row["source"]), int(row["target"]), row["timestamp"], -row["weight"]))
    
    for index, row in undirected_df.iterrows():
        if( - threshold) <= row["weight"] <= threshold:
            undirected_neut_graph.add_edge((int(row["source"]), int(row["target"]), row["timestamp"]))
        elif row["weight"] > threshold:
            undirected_pos_graph.add_edge((int(row["source"]), int(row["target"]), row["timestamp"], row["weight"]))
        else:
            undirected_neg_graph.add_edge((int(row["source"]), int(row["target"]), row["timestamp"], -row["weight"]))
    directed_neut_graph_edgelist = directed_neut_graph.get_edgelist()
    d_neutral_path = os.path.join(config["dataset"]["output_dir"], "graphs", "temporal", "edgelists", "sentiment_directed_neutral.csv")
    save_temporal_graph(d_neutral_path, directed_neut_graph_edgelist, False)

    directed_pos_graph_edgelist = directed_pos_graph.get_edgelist(data=True)
    d_positive_path = os.path.join(config["dataset"]["output_dir"], "graphs", "temporal", "edgelists", "sentiment_directed_positive.csv")
    save_temporal_graph(d_positive_path, directed_pos_graph_edgelist, True)

    directed_neg_graph_edgelist = directed_neg_graph.get_edgelist(data=True)
    d_negative_path = os.path.join(config["dataset"]["output_dir"], "graphs", "temporal", "edgelists", "sentiment_directed_negative.csv")
    save_temporal_graph(d_negative_path, directed_neg_graph_edgelist, True)

    undirected_neut_graph_edgelist = undirected_neut_graph.get_edgelist()
    und_neutral_path = os.path.join(config["dataset"]["output_dir"], "graphs", "temporal", "edgelists", "sentiment_undirected_neutral.csv")
    save_temporal_graph(und_neutral_path, undirected_neut_graph_edgelist, False)

    undirected_pos_graph_edgelist = undirected_pos_graph.get_edgelist(data=True)
    und_positive_path = os.path.join(config["dataset"]["output_dir"], "graphs", "temporal", "edgelists", "sentiment_undirected_positive.csv")
    save_temporal_graph(und_positive_path, undirected_pos_graph_edgelist, True)

    undirected_neg_graph_edgelist = undirected_neg_graph.get_edgelist(data=True)
    und_negative_path = os.path.join(config["dataset"]["output_dir"], "graphs", "temporal", "edgelists", "sentiment_undirected_negative.csv")
    save_temporal_graph(und_negative_path, undirected_neg_graph_edgelist, True)
    



            
    


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config',default='wundt/multiview/preprocess/config.yml')
    args = parser.parse_args()
    main(args)