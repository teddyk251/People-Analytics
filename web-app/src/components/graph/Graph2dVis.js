import "react-vis/dist/style.css";
import React from "react";
import { XYPlot, XAxis, YAxis, HorizontalGridLines, VerticalGridLines, LineMarkSeries, DiscreteColorLegend } from 'react-vis';

class Graph2dVis extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            data: props.data,
            bc_selected:true,
            cc_selected: true,
            evc_selected:true
        }
        this.onLineSeriesClick = props.onLineSeriesClick;
        this.toggleBC = this.toggleBC.bind(this);
        this.toggleCC = this.toggleCC.bind(this);
        this.toggleEVC = this.toggleEVC.bind(this);


    }

     toggleBC(event){
            this.setState({bc_selected:!this.state.bc_selected});
        }
    toggleCC(event){
            this.setState({cc_selected:!this.state.cc_selected});
        }
    toggleEVC(event){
            this.setState({evc_selected:!this.state.evc_selected});
        }
    render() {
        
        const legendItems = [
            {
                title: 'Betweenness centrality',
                color: 'blue',
                strokeWidth: 6,
            },
            {
                title: 'Closeness centrality',
                color: 'red',
                strokeWidth: 6,
            },
            {
                title: 'Eigen Vector centrality',
                color: 'yellow',
                strokeWidth: 6,
            },
        ]

       

        return (
            <div>
                {
                    this.props.selected_node != null
                        ? <h6>Centrality scores of: {this.props.selected_node.label} </h6>
                        : <h6> Centrality scores </h6>
                    
                }
                <div id="instanceCheckboxes" style={{ display: 'inline-flex', flexDirection: 'row'  }}>
                    <input type={"checkbox"} onChange={this.toggleBC} style={{ width: "23px", height: "23px", marginTop: 5 }}  checked={this.state.bc_selected}/><span style={{marginRight:10}}> B.C </span> 
                    <input type={"checkbox"} onChange={this.toggleCC} style={{ width: "23px", height: "23px", marginTop: 5 }} checked={this.state.cc_selected}/><span style={{marginRight:10}}> C.C </span> 
                    <input type={"checkbox"} onChange={this.toggleEVC} style={{ width: "23px", height: "23px", marginTop: 5 }} checked={this.state.evc_selected}/><span style={{marginRight:10}}> Ev.C </span> 
                    
                </div>
                < XYPlot height={600} width={800} className="Graph2DVisualizer">
                    <DiscreteColorLegend items={legendItems} />
                    <VerticalGridLines />
                    <HorizontalGridLines />
                    <XAxis />
                    <YAxis />
                    {
                        this.state.bc_selected&&<LineMarkSeries label={"Betweenness centrality"} color={"blue"} curve={"curveMonotoneX"} onValueClick={this.onLineSeriesClick} data={this.props.data.bc.map((item, i) => { return ({ x: i, y: item }) })} />
                    }
                    {
                        this.state.cc_selected&&<LineMarkSeries label={"Closeness centrality"} color={"red"} curve={"curveMonotoneX"} onValueClick={this.onLineSeriesClick} data={this.props.data.cc.map((item, i) => { return ({ x: i, y: item }) })} />
                    }
                    {
                        this.state.evc_selected && <LineMarkSeries label={"Eigen Vector centrality"} color={"yellow"} curve={"curveMonotoneX"} onValueClick={this.onLineSeriesClick} data={this.props.data.evc.map((item, i) => { return ({ x: i, y: item }) })} />
                    }
                    
                    
                    
                </XYPlot >
            </div>
            )
    }
}

export default Graph2dVis;