import json

from bson import json_util
from dicttoxml import dicttoxml
from flask import request, Response
from flask_restx import Namespace, fields, Resource

from lib.ApiRequests import JSONApiRequest
from lib.DatabaseHandler import DatabaseHandler
from lib.DatabaseLayer import getDBStats
from web.home.utils import filter_logic, parse_headers
from web.restapi.cpe_convert import message
from web.restapi.cve import cve_last_entries

api = Namespace(
    "query", description="Endpoints for querying the cve search database", path="/"
)


query_entries = api.model(
    "QueryEntries",
    {
        "results": fields.List(
            fields.Nested(cve_last_entries),
            description="Results from query",
            example="",
        ),
        "total": fields.Integer(
            description="Total amount of records available for this query",
            example="150243",
        ),
    },
)

database_inner = api.model(
    "DBInner",
    {
        "last_update": fields.DateTime(
            description="Date time of last update", example="2019-09-30T18:53:48"
        ),
        "size": fields.Integer(
            description="Amount of documents in collection", example="570",
        ),
    },
)

database_wild = fields.Wildcard(
    fields.Nested(database_inner),
    description="Database collection mapping id",
    skip_none=True,
)

database_entry = api.model("documents", {"*": database_wild},)

PostBodyRequest = api.model(
    "ApiPostRequest",
    {
        "retrieve": fields.String(
            description="Retrieve data from this collection, allowed options are 'capec', 'cpe', 'cves', 'cwe', 'via4'",
            example="cves",
            required=True,
        ),
        "dict_filter": fields.Raw(
            description="filter according to pymongo docs",
            example={
                "vulnerable_configuration": "cpe:2.3:o:microsoft:windows_7:*:sp1:*:*:*:*:*:*"
            },
            required=True,
        ),
        "limit": fields.Integer(
            description="Limit the amount of returned documents", example=10,
        ),
        "skip": fields.Integer(
            description="Skip the first N amount of documents", example=25,
        ),
        "sort": fields.String(description="Sort on this field", example="cvss",),
        "sort_dir": fields.String(
            description="sorting direction ASC = pymongo.ASCENDING, DESC = pymongo.DESCENDING",
            example="ASC",
        ),
        "query_filter": fields.Raw(
            description="query filter to exclude certain fields (via a 0) or to limit query to a specific set (via a 1)",
            example={"access": 0, "cwe": 0},
        ),
        "output_format": fields.String(
            description="define the desired output format JSON by default, XML supported",
            example="json",
        ),
    },
)

PostBodyResponse = api.model(
    "ApiPostResponse",
    {
        "data": fields.List(
            fields.Raw,
            description="Returned data",
            example=[
                {
                    "Modified": "2017-08-15T17:24:00",
                    "Published": "2017-08-08T21:29:00",
                    "_id": "5f76228ff3b9be1242eb4fc0",
                    "assigner": "cve@mitre.org",
                    "cvss": 9.3,
                    "impactScore": 3.0,
                    "exploitabilityScore": 3.0,
                    "cvss-time": "2017-08-15T17:24:00",
                    "cvss-vector": "AV:N/AC:M/Au:N/C:C/I:C/A:C",
                    "id": "CVE-2017-0250",
                    "impact": {
                        "availability": "COMPLETE",
                        "confidentiality": "COMPLETE",
                        "integrity": "COMPLETE",
                    },
                    "impact3": {
                        "availability": "HIGH",
                        "confidentiality": "HIGH",
                        "integrity": "HIGH",
                    },
                    "exploitability3": {
                        "attackvector": "NETWORK",
                        "attackcomplexity": "LOW",
                        "privilegesrequired": "NONE",
                        "userinteraction": "REQUIRED",
                        "scope": "CHANGED",
                    },
                    "cvss3": 9.6,
                    "impactScore3": 3.0,
                    "exploitabilityScore3": 6.6,
                    "cvss3-vector": "CVSS:3.0/AV:N/AC:L/PR:N/UI:R/S:C/C:H/I:H/A:H",
                    "last-modified": "2017-08-15T17:24:00",
                    "references": [
                        "http://www.securityfocus.com/bid/98100",
                        "http://www.securitytracker.com/id/1039090",
                        "https://portal.msrc.microsoft.com/en-US/security-guidance/advisory/CVE-2017-0250",
                    ],
                    "summary": "Microsoft JET Database Engine in Windows Server 2008 SP2 and R2 SP1, Windows 7 SP1, "
                    "Windows 8.1, Windows Server 2012 Gold and R2, Windows RT 8.1, Windows 10 Gold, 1511, "
                    "1607, 1703, and Windows Server 2016 allows a remote code execution vulnerability due "
                    'to buffer overflow, aka "Microsoft JET Database Engine Remote Code Execution '
                    'Vulnerability".',
                    "vulnerable_configuration": [
                        "cpe:2.3:o:microsoft:windows_10:-:*:*:*:*:*:*:*",
                        "cpe:2.3:o:microsoft:windows_10:1511:*:*:*:*:*:*:*",
                        "cpe:2.3:o:microsoft:windows_10:1607:*:*:*:*:*:*:*",
                        "cpe:2.3:o:microsoft:windows_10:1703:*:*:*:*:*:*:*",
                        "cpe:2.3:o:microsoft:windows_7:*:sp1:*:*:*:*:*:*",
                        "cpe:2.3:o:microsoft:windows_8.1:*:*:*:*:*:*:*:*",
                        "cpe:2.3:o:microsoft:windows_rt_8.1:*:*:*:*:*:*:*:*",
                        "cpe:2.3:o:microsoft:windows_server_2008:*:sp2:*:*:*:*:*:*",
                        "cpe:2.3:o:microsoft:windows_server_2008:r2:sp1:*:*:*:*:*:*",
                        "cpe:2.3:o:microsoft:windows_server_2012:*:*:*:*:*:*:*:*",
                        "cpe:2.3:o:microsoft:windows_server_2012:r2:*:*:*:*:*:*:*",
                        "cpe:2.3:o:microsoft:windows_server_2016:*:*:*:*:*:*:*:*",
                    ],
                    "vulnerable_configuration_cpe_2_2": [],
                    "vulnerable_product": [
                        "cpe:2.3:o:microsoft:windows_10:-:*:*:*:*:*:*:*",
                        "cpe:2.3:o:microsoft:windows_10:1511:*:*:*:*:*:*:*",
                        "cpe:2.3:o:microsoft:windows_10:1607:*:*:*:*:*:*:*",
                        "cpe:2.3:o:microsoft:windows_10:1703:*:*:*:*:*:*:*",
                        "cpe:2.3:o:microsoft:windows_7:*:sp1:*:*:*:*:*:*",
                        "cpe:2.3:o:microsoft:windows_8.1:*:*:*:*:*:*:*:*",
                        "cpe:2.3:o:microsoft:windows_rt_8.1:*:*:*:*:*:*:*:*",
                        "cpe:2.3:o:microsoft:windows_server_2008:*:sp2:*:*:*:*:*:*",
                        "cpe:2.3:o:microsoft:windows_server_2008:r2:sp1:*:*:*:*:*:*",
                        "cpe:2.3:o:microsoft:windows_server_2012:*:*:*:*:*:*:*:*",
                        "cpe:2.3:o:microsoft:windows_server_2012:r2:*:*:*:*:*:*:*",
                        "cpe:2.3:o:microsoft:windows_server_2016:*:*:*:*:*:*:*:*",
                    ],
                },
                {
                    "Modified": "2019-10-03T00:03:00",
                    "Published": "2017-06-15T01:29:00",
                    "_id": "5f76228f56409e4ec0eb4f57",
                    "assigner": "cve@mitre.org",
                    "cvss": 9.3,
                    "impactScore": 3.0,
                    "exploitabilityScore": 3.0,
                    "cvss-time": "2019-10-03T00:03:00",
                    "cvss-vector": "AV:N/AC:M/Au:N/C:C/I:C/A:C",
                    "id": "CVE-2017-0260",
                    "impact": {
                        "availability": "COMPLETE",
                        "confidentiality": "COMPLETE",
                        "integrity": "COMPLETE",
                    },
                    "impact3": {
                        "availability": "HIGH",
                        "confidentiality": "HIGH",
                        "integrity": "HIGH",
                    },
                    "exploitability3": {
                        "attackvector": "NETWORK",
                        "attackcomplexity": "LOW",
                        "privilegesrequired": "NONE",
                        "userinteraction": "REQUIRED",
                        "scope": "CHANGED",
                    },
                    "cvss3": 9.6,
                    "impactScore3": 3.0,
                    "exploitabilityScore3": 6.6,
                    "cvss3-vector": "CVSS:3.0/AV:N/AC:L/PR:N/UI:R/S:C/C:H/I:H/A:H",
                    "last-modified": "2019-10-03T00:03:00",
                    "references": [
                        "http://www.securityfocus.com/bid/98810",
                        "http://www.securitytracker.com/id/1038668",
                        "https://portal.msrc.microsoft.com/en-US/security-guidance/advisory/CVE-2017-0260",
                    ],
                    "summary": "A remote code execution vulnerability exists in Microsoft Office when the software "
                    'fails to properly handle objects in memory, aka "Office Remote Code Execution '
                    'Vulnerability". This CVE ID is unique from CVE-2017-8509, CVE-2017-8510, '
                    "CVE-2017-8511, CVE-2017-8512, and CVE-2017-8506.",
                    "vulnerable_configuration": [
                        "cpe:2.3:a:microsoft:office:2013:sp1:*:*:*:*:*:*",
                        "cpe:2.3:a:microsoft:office:2016:*:*:*:*:*:*:*",
                        "cpe:2.3:o:microsoft:windows_7:*:sp1:*:*:*:*:*:*",
                        "cpe:2.3:o:microsoft:windows_server_2008:*:sp2:*:*:*:*:*:*",
                        "cpe:2.3:o:microsoft:windows_server_2008:r2:sp1:*:*:*:*:*:*",
                    ],
                    "vulnerable_configuration_cpe_2_2": [],
                    "vulnerable_product": [
                        "cpe:2.3:a:microsoft:office:2013:sp1:*:*:*:*:*:*",
                        "cpe:2.3:a:microsoft:office:2016:*:*:*:*:*:*:*",
                        "cpe:2.3:o:microsoft:windows_7:*:sp1:*:*:*:*:*:*",
                        "cpe:2.3:o:microsoft:windows_server_2008:*:sp2:*:*:*:*:*:*",
                        "cpe:2.3:o:microsoft:windows_server_2008:r2:sp1:*:*:*:*:*:*",
                    ],
                },
            ],
        ),
        "total": fields.Integer(
            description="Total amount of returned documents", example=2,
        ),
    },
)


@api.route("/query")
@api.response(400, "Error processing request", model=message)
@api.response(500, "Server error", model=message)
class QueryApi(Resource):
    @api.param(
        "rejected",
        "Hide or show rejected CVEs",
        example="hide/show",
        default="show",
        _in="header",
    )
    @api.param("cvss_score", "CVSS score", example=6.8, _in="header")
    @api.param(
        "cvss_modifier",
        "Select the CVSS score of the CVEs related to cvss_score",
        example="above/equals/below",
        _in="header",
    )
    @api.param(
        "time_start",
        "Earliest time for a CVE",
        example="dd-mm-yyyy or dd-mm-yy format, using - or /",
        _in="header",
    )
    @api.param(
        "time_end",
        "Latest time for a CVE",
        example="dd-mm-yyyy or dd-mm-yy format, using - or /",
        _in="header",
    )
    @api.param(
        "time_modifier",
        "Timeframe for the CVEs, related to the start and end time",
        example="from/until/between/outside",
        _in="header",
    )
    @api.param(
        "time_type",
        "Select which time is used for the filter",
        example="Modified/Published/last-modified",
        _in="header",
    )
    @api.param(
        "skip", "Skip the n latest vulnerabilities", example=50, _in="header", type=int,
    )
    @api.param(
        "limit",
        "Limit the amount of vulnerabilities to return",
        example=20,
        _in="header",
        type=int,
    )
    @api.marshal_with(query_entries, skip_none=True)
    def get(self):
        """
        Query for CVE's

        Returns a list of CVEs matching the criteria of the filters specified in the headers.
        """
        f = {
            "rejectedSelect": request.headers.get("rejected"),
            "cvss": request.headers.get("cvss_score"),
            "cvssSelect": request.headers.get("cvss_modifier"),
            "startDate": request.headers.get("time_start"),
            "endDate": request.headers.get("time_end"),
            "timeSelect": request.headers.get("time_modifier"),
            "timeTypeSelect": request.headers.get("time_type"),
            "skip": request.headers.get("skip"),
            "limit": request.headers.get("limit"),
        }

        try:
            skip = int(f["skip"]) if f["skip"] else 0
        except ValueError:
            api.abort(400, "Skip variable should be an integer")

        try:
            limit = int(f["limit"]) if f["limit"] else 0
        except ValueError:
            api.abort(400, "Limit variable should be an integer")

        results = filter_logic(f, skip, limit)

        if len(results) == 0:
            api.abort(404, "")
        else:
            return results

    @api.doc(body=PostBodyRequest)
    @api.response(200, "OK", PostBodyResponse)
    @api.param(
        "format",
        "Specify in which format the results must be returned",
        example="json/xml",
        default="json",
        _in="query",
    )
    def post(self, format_output="json"):
        """
        Free query

        Api endpoint that can be used to freely (within the allowed parameters) query the cve search database.

        The request sample payload displays a request body for a single query; multiple request can be combined within
        a comma separated list and send in a single request. In this case the responses will be send back in a list.
        For each request a separate list entry with the results.
        """
        headers = parse_headers(request.headers)
        database_connection = DatabaseHandler()

        output_format = ["json", "xml"]

        received_format = request.args.get("format", None)

        if received_format is None:
            format_output = format_output
        else:
            format_output = str(received_format)

        if format_output not in output_format:
            api.abort(
                400,
                "Specified output format is not possible; possible options are: {}!".format(
                    output_format
                ),
            )

        try:
            body = request.json
        except Exception:
            return "Could not parse request body", 400

        if isinstance(body, dict):
            result = database_connection.handle_api_json_query(
                JSONApiRequest(headers=headers, body=body)
            )
        elif isinstance(body, list):
            result = []
            for each in body:
                result.append(
                    database_connection.handle_api_json_query(
                        JSONApiRequest(headers=headers, body=each)
                    )
                )

        if isinstance(result, tuple):
            # error response; just return it
            return result
        else:
            if format_output == "json":
                return Response(
                    json.dumps(
                        result, indent=4, sort_keys=True, default=json_util.default,
                    ),
                    mimetype="application/json",
                )
            if format_output == "xml":
                return Response(dicttoxml(result), mimetype="text/xml")


@api.route("/dbinfo")
@api.response(400, "Error processing request", model=message)
@api.response(500, "Server error", model=message)
class DBInfo(Resource):
    @api.marshal_with(database_entry)
    def get(self):
        """
        Get Database info

        Returns the stats of the database. When the user authenticates, more information is returned.

        This information includes:
        <ul>
          <li> Amount of whitelist and blacklist records </li>
          <li> Some server settings like the database name </li>
          <li> Some database information like disk usage </li>
        </ul>
        Unauthenticated queries return only collection information.
        """
        return getDBStats()
