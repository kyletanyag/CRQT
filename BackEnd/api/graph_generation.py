'''
@author Thomas Laverghetta
@brief This is the logical attack graph (LAG) generation module. It will accept csv files from front-end which contain vertices and edges for user provided network. 

'''
from flask import Blueprint, jsonify, request
from .nvd import data_driven_cvss_query, model_driven_cvss_query
import enum
from collections import deque
from .analysis import DataDriven, DerivedScore

# route for LAG generation module
graph_bp = Blueprint('graph_bp', __name__)

@graph_bp.route('/network_topology_data_driven_input', methods=['POST'])
def network_topology_data_driven_input():
    network = request.get_json()  # json network topology data driven
    
    lag = {}

    # vertices
    for node in network["vertices"]:
        node_id = int(node["id"])
        lag[node_id] = DataDriven.Node()

        # setting logic
        if node["logic"] == "FLOW":
            lag[node_id].node_logic = DataDriven.Node_Logic.FLOW 
        elif node["logic"] == "AND":
            lag[node_id].node_logic = DataDriven.Node_Logic.AND
        elif node["logic"] == "OR":
            lag[node_id].node_logic = DataDriven.Node_Logic.OR
        else:
            lag[node_id].node_logic = DataDriven.Node_Logic.LEAF

        # checking if derivation node
        if node["description"][:3] == 'RULE':
            lag[node_id].node_type = DataDriven.Node_Type.DERIVATION
            for score in lag[node_id].derived_score:
                score = network["sim_config"][0]["derivation_node_prob"]

        # checking if primitive fact node (primitive fact nodes are always leafs)
        elif lag[node_id].node_logic == DataDriven.Node_Logic.LEAF: 
            lag[node_id].node_type = DataDriven.Node_Type.PRIMITIVE_FACT

        # else, derived fact node
        else:
            lag[node_id].node_type = DataDriven.Node_Type.DERIVED
        
        # checking if node is execCode
        if lag[node_id].node_type == DataDriven.Node_Type.DERIVATION:
            execCode_index = node["description"].find('execCode')
            if execCode_index != -1:
                # if execCode node, flag
                lag[node_id].isExecCode = True

    # edges
    for edge in network["arcs"]:
        lag[int(edge["currNode"])].next_node.append(int(edge["nextNode"])) 
        lag[int(edge["nextNode"])].calculations_remaining += 1              # increase number of nodes needed for calculation

    # constructing queue for leaf nodes for derived score calculations
    leaf_queue = deque()
    for key in lag:
        if lag[key].node_type == DataDriven.Node_Type.PRIMITIVE_FACT:
            # searching for CVE ID
            cve_index = node["description"].find('CVE')
            if cve_index != -1:
                # getting CVSS scores
                lag[key].derived_score = data_driven_cvss_query(node["description"][cve_index:(cve_index+13)])
            # else use default values (1.0)
            leaf_queue.append(lag[key])

    lag = DerivedScore(lag, leaf_queue)

    # converting to JSON
    node_type_to_str = {
        DataDriven.Node_Type.DERIVATION : 'Derivation', 
        DataDriven.Node_Type.DERIVED : 'Derived Fact',
        DataDriven.Node_Type.PRIMITIVE_FACT: 'Primitive Fact'}

    vertices = []
    edges = []
    for key in lag:
        vertices.append({
                'id' : key,
                'node_type' : node_type_to_str[lag[key].node_type], 
                'base_score' : lag[key].derived_score[0],
                'exploitability_score' : lag[key].derived_score[1],
                'impact_score' : lag[key].derived_score[2]})
        for e in lag[key].next_node:
            edges.append({'source' : key, 'target' : e})
    
    return jsonify({'nodes': vertices, 'edges' : edges})

        

@graph_bp.route('/network_topology_model_driven_input', methods=['POST'])
def network_topology_model_driven_input():
    print ('Hello FUCKERS!')
    return {'message': 'Hello!'}