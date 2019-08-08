import argparse
from tgraphs import datastructures
from pydoc import locate
import networkx as nx
import os
from collections import defaultdict
import json

def build_snapshot_graphs(args):
    snapshot_index = 0
    output = {}
    while os.path.exists(os.path.join(args.graphs_path, "snapshot-%d.csv" % snapshot_index)):
        snapshot_file_path = os.path.join(args.graphs_path, "snapshot-%d.csv" % snapshot_index)
        graph_base = None
        if args.directed:
            graph_base = nx.DiGraph()
        else:
            graph_base = nx.Graph()
        data_arg = False
        if args.graph_type == "weighted" or args.graph_type == "multiplex":
            data_arg = {"wieght":args.weight_type}
        with open(snapshot_file_path, "rb") as graph_file:
            next(graph_file)
            snapshot_graph = nx.read_edgelist(graph_file, delimiter=",", create_using=graph_base, nodetype=int, data=data_arg)
            output[snapshot_index] = snapshot_graph
        snapshot_index += 1
        
    return output, snapshot_index
def get_temporal_node_bc_scores(args, snapshot_graphs, num_graphs,all_nodes):
    output =defaultdict(lambda: defaultdict(list))
    for i in range(num_graphs):
        current_bc_scores = nx.algorithms.centrality.betweenness_centrality(snapshot_graphs[i], weight=args.weighted)
        current_cc_scores = nx.algorithms.centrality.closeness_centrality(snapshot_graphs[i])
        current_evc_scores = nx.algorithms.centrality.eigenvector_centrality(snapshot_graphs[i], weight=args.weighted)
        for node in all_nodes:
            if node in current_bc_scores:
                output["betweenness_centrality"][node].append(current_bc_scores[node])
                output["closeness_centrality"][node].append(current_cc_scores[node])
                output["eigenvector_centrality"][node].append(current_evc_scores[node])
            else:
                output["betweenness_centrality"][node].append(0.0)
                output["closeness_centrality"][node].append(0.0)
                output["eigenvector_centrality"][node].append(0.0)
                
    return output


def main(args):
    all_nodes = set()
    s_graphs, num_graphs = build_snapshot_graphs(args)
    for graph in s_graphs:
        all_nodes = all_nodes.union(set(s_graphs[graph].nodes))
    node_scores = get_temporal_node_bc_scores(args, s_graphs, num_graphs, all_nodes)


    if not os.path.exists(args.output_dir):
        os.mkdir(args.output_dir)
    output = {}
    for centrality in node_scores:
        output[centrality]={}
        for node in node_scores[centrality]:
            output[centrality][node] = node_scores[centrality][node]
    graphs_path = args.graphs_path
    if graphs_path[-1] == "/":
        graphs_path = graphs_path[:-1]
    _, folder = os.path.split(graphs_path)
    with open(os.path.join(args.output_dir, folder + ".json"), "w+") as output_file:
        json.dump(output, output_file)

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--graphs_path', required=True, type=str)
    parser.add_argument('-t', '--graph_type', required=True, choices=["unweighted", "weighted", "multiplex"])
    parser.add_argument('-r', '--weight_type', default=int, type=locate, choices=[int, float])
    parser.add_argument('-d', '--directed', action='store_true')
    parser.add_argument('-w', '--weighted', action='store_true')
    parser.add_argument('-o', '--output_dir', required=True)

    
    
    args = parser.parse_args()
    main(args)