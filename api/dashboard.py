from flask import (
    Blueprint, flash, render_template, request, jsonify
)
from api.utilities import network_factory as nf
from api.utilities.ncfdlt_model import NCFDLT
from api.utilities.diffusion_model import QuiescentFunction
from api.utilities.npcfdlt_model import NPDLT
from api.utilities.spcfdlt_model import SPDLT
from networkx import NetworkXError

db = Blueprint('main', __name__)

@db.route('/', methods=('GET', ))
def index():
    return render_template('index.html')


@db.route('/getNetwork/<int:n>/<int:e>/<int:m>', methods=('GET',))
def getNetwork(n, e, m):
    try:
        G = nf.create_network(n, e, m)
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

