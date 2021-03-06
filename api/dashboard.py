from flask import (
    Blueprint, flash, render_template, request, jsonify
)
from api.utilities import network_factory as nf
from api.utilities.ncfdlt_model import NCFDLT
from api.utilities.diffusion_model import QuiescentFunction
from api.utilities.npcfdlt_model import NPDLT
from api.utilities.spcfdlt_model import SPDLT
from networkx import NetworkXError
import os

db = Blueprint('main', __name__)

ALLOWED_EXTENSIONS = ['ncol', 'edgelist', 'txt']
MAX_FILE_SIZE = 5e+5  # 500kB


def allowed(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@db.route('/', methods=('GET',))
def index():
    return render_template('index.html')


@db.route('/getNetwork/<int:n>/<int:e>/<int:m>/<int:perc>', methods=('GET', 'POST'))
def getNetwork(n, e, m, perc):
    try:
        if request.method == 'POST':
            file = request.files['files']
            if file.filename == '':
                return jsonify(success=0, msg="No selected file")
            if not allowed(file.filename):
                return jsonify(success=0, msg="File not allowed")
            blob = file.read()
            if len(blob) > MAX_FILE_SIZE:
                return jsonify(success=0, msg="File size must be below 2Mb")
            G = nf.read_file(blob)
        else:
            G = nf.create_network(n, e, m, perc/100)
    except NetworkXError as e:
        return jsonify(success=0, msg=str(e))

    return jsonify(success=1, data=G)


@db.route('/run', methods=('POST',))
def run():
    request_json = request.get_json()
    active_nodes, edges, model_ = request_json['active'], request_json['edges'], int(request_json['model'])
    G = nf.convertedgelist2digraph(edges)
    # non competitive
    if model_ == 0:
        model = NCFDLT(G, QuiescentFunction())
        model.set_seed_set([u for u, s in active_nodes])
    else:
        # semi progressive
        if model_ == 1:
            model = SPDLT(G)
        else:
            model = NPDLT(G)

        active, activeComp = [], []
        for v, s in active_nodes:
            if s == "active":
                active.append(v)
            else:
                activeComp.append(v)

        model.set_seed_set(active, 1)
        model.set_seed_set(activeComp, 2)

    transitions = model.run()
    return jsonify(transitions)


@db.route('/about', methods=('GET',))
def about():
    return render_template('about.html')


@db.route('/team', methods=('GET',))
def team():
    return render_template('team.html')
