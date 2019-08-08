import React from "react"
import "./Modal.css"

class Modal extends React.Component{
    constructor(props) {
        super(props);
    }
    render() {

        const modal_style = {
            transform: this.props.show ? 'translateY(0vh)' : 'translateY(-100vh)',
            opacity: this.props.show ? '1' : '0'
        }
        return (
            <div>
                <div className="modal-wrapper" style={modal_style}>
                    <div className="modal-header">
                        <h3>Modal Header</h3>
                        <span className="close-modal-btn" onClick={this.props.close}>×</span>
                    </div>
                    <div className="modal-body">
                        <p>
                            {this.props.children}
                        </p>
                    </div>
                    <div className="modal-footer">
                        <button className="btn-cancel" onClick={this.props.close}>CLOSE</button>
                        <button className="btn-continue">CONTINUE</button>
                    </div>
                </div>
            </div>
        )
    }
}
export default Modal;