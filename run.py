import ast

import ravop.core as R
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from ravcom import RavQueue, QUEUE_HIGH_PRIORITY, QUEUE_LOW_PRIORITY, RDF_MYSQL_USER, \
    RDF_MYSQL_DATABASE, RDF_MYSQL_PASSWORD, RDF_MYSQL_PORT, RDF_MYSQL_HOST
from ravcom import ravcom
from ravop.core import Graph

app = Flask(__name__, static_folder='static')
app.config["DEBUG"] = True
RDF_DATABASE_URI = 'mysql://{}:{}@{}:{}/{}?host={}?port={}'.format(RDF_MYSQL_USER, RDF_MYSQL_PASSWORD,
                                                                   RDF_MYSQL_HOST, RDF_MYSQL_PORT,
                                                                   RDF_MYSQL_DATABASE,
                                                                   RDF_MYSQL_HOST, RDF_MYSQL_PORT)
app.config['SQLALCHEMY_DATABASE_URI'] = RDF_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

queue_high_priority = RavQueue(name=QUEUE_HIGH_PRIORITY)
queue_low_priority = RavQueue(name=QUEUE_LOW_PRIORITY)


def get_queued_ops():
    high_priority_ops = []
    for i in range(queue_high_priority.__len__()):
        high_priority_ops.append(queue_high_priority.get(i))

    low_priority_ops = []
    for i in range(queue_low_priority.__len__()):
        low_priority_ops.append(queue_low_priority.get(i))

    return high_priority_ops, low_priority_ops


@app.route('/')
def home():
    high_priority_ops, low_priority_ops = get_queued_ops()
    return render_template('home.html', high_priority_ops=high_priority_ops, low_priority_ops=low_priority_ops)


@app.route('/clients')
def clients():
    clients = ravcom.get_all_clients()
    clients_list = []
    for client in clients:
        clients_list.append(client.__dict__)
    return render_template('clients.html', clients=clients_list)


@app.route('/graphs')
def graphs():
    graphs = ravcom.get_all_graphs()
    graphs_list = []
    for graph in graphs:
        progress = Graph(id=graph.id).progress
        graph_dict = graph.__dict__
        graph_dict['progress'] = progress
        graphs_list.append(graph_dict)
    return render_template('graphs.html', graphs=graphs_list)


@app.route('/ops')
def ops():
    ops = ravcom.get_all_ops()
    ops_list = []
    for op in ops:
        op_dict = op.__dict__
        op_dict = parse_op_inputs_outputs(op_dict)
        ops_list.append(op_dict)
    return render_template('ops.html', ops=ops_list)


@app.route('/graph/vis')
def graph_vis():
    return render_template('graph_vis.html')


@app.route('/graph/ops/<graph_id>/')
def graph_ops(graph_id):
    ops = ravcom.get_ops(graph_id=graph_id)
    ops_list = []
    for op in ops:
        op_dict = op.__dict__
        op_dict = parse_op_inputs_outputs(op_dict)
        ops_list.append(op_dict)
    return render_template('graph_ops.html', ops=ops_list)


@app.route('/graph/ops/<graph_id>/<graph_op_id>/')
def graph_op_viewer(graph_id, graph_op_id):
    op = ravcom.get_op(op_id=graph_op_id)
    op_dict = op.__dict__
    op_dict = parse_op_inputs_outputs(op_dict)
    return render_template('op_viewer.html', op=op_dict)


@app.route('/data/<data_id>/')
def data_viewer(data_id):
    data_dict = {}
    data = ravcom.get_data(data_id=data_id)
    data = R.Data(id=data_id)
    print(data.__dict__)
    if type(data.value).__name__ == 'float' or type(data.value).__name__ == 'int':
        data_dict['output'] = data.value
        data_dict['shape'] = 1
    else:
        data_dict['output'] = data.value.tolist()
        data_dict['shape'] = data.value.shape
    return render_template('data_viewer.html', data=data_dict)


@app.route('/graph/<graph_id>/')
def graph_viewer(graph_id):
    graph = ravcom.get_graph(graph_id=graph_id)
    return render_template('graph_viewer.html', graph=graph.__dict__)


def parse_op_inputs_outputs(op_dict):
    print(op_dict['inputs'])
    if op_dict.get("inputs") is not None and op_dict.get("inputs") != "null":
        inputs = ast.literal_eval(op_dict['inputs'])
        inputs_list = []
        for op_id in inputs:
            inputs_list.append(ravcom.get_op(op_id=op_id).__dict__)
        op_dict['inputs'] = inputs_list
    else:
        op_dict["inputs"] = []

    if op_dict.get("outputs") is not None and op_dict.get("outputs") != "null":
        outputs = ast.literal_eval(op_dict['outputs'])
        outputs_list = []
        for data_id in outputs:
            outputs_list.append(ravcom.get_data(data_id=data_id).__dict__)
        op_dict['outputs'] = outputs_list
    else:
        op_dict['outputs'] = []

    return op_dict


if __name__ == '__main__':
    app.run()
