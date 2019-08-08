import React from "react";
import vis from "vis"
import './GraphVisualizer.css';


class GraphVisualizer extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            edges: props.edges,
            nodes: props.nodes,
            showNodeScoreDiagram:props.showNodeScoreDiagram
        }
        console.log("graph_name", props.graph_name)
    }
    componentDidMount() {
        const data = { nodes: this.state.nodes, edges: this.state.edges };
        const options = {};
        const network = new vis.Network(this.refs.container, data, options);
        network.on("stabilizationIterationsDone", function () {
            network.setOptions({ physics: false });
        });
        let $this = this;
        network.on('click', function (properties) {
            let node_ids = properties.nodes;
            $this.state.showNodeScoreDiagram(node_ids);
            if (node_ids.length > 0) {
                
            }

        });
    }

    render() {
        
        return (
            <div>
                <div ref="container" className="GraphVisualizer" >
                </div>
                <h4 >Graph: {this.props.graph_name}</h4>
            </div>
            
            
        );
    }
}

export default GraphVisualizer;