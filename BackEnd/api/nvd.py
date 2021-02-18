'''
@author Thomas Laverghetta
@brief this file contains processes to communicate with local NVD. 

'''

from flask import Blueprint, jsonify, request
from .data_models import NVD

nvd_bp = Blueprint('nvd_bp', __name__)

class CVSS:
    base_score = float()
    exploitabiliy_score_v2 = float()
    impact = float()

# query with database to get cve_ids
@nvd_bp.route('/cvss_query')
def cvss_query(cve_ids):
    scores = []
    for cve_id in cve_ids:
        nvd = NVD.query.get(cve_id)
        scores.append(CVSS(base_score=nvd.base_score, exploitabiliy_score_v2=nvd.exploitabiliy_score_v2,impact=nvd.impact_score_v2))

    return scores
    # for data in nvd.query.filter(nvd["cve id"]).all():
    #     if cve_ids == data:
    #         print(nvd[data].cveid, nvd[data].basescore, nvd[data].exploitability, nvd[data].discription)
    #     else:
    #         print("CVE ID not found")
    #         return nvd.query.filterby(nvd['cve id']==cve_ids).first_or_404()


# updates database with latest nvd
@nvd_bp.route('/update_nvd')
def update_nvd(cve_ids):
    for data in nvd.query.filter(nvd["cve id"]).all():
        if cve_ids not in data:
            nvd.add(cve_ids)
            nvd.commit()
