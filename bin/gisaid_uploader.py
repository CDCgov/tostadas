#!/usr/bin/env python3

"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

version = "1.0.3"

import argparse, getpass, sys, requests, secrets, hashlib, json, time, csv, os
from itertools import islice

# global configuration
GPS_SERVICE_URL_TEST = "https://gpsapi-test.epicov.org/epi3/gps_api"
GPS_SERVICE_URL_LOCAL = "http://localhost:8080/epi3/gps_api"
GPS_SERVICE_URL = "https://gpsapi.epicov.org/epi3/gps_api"


# parse CLI-arguments
parser = argparse.ArgumentParser()

parser.add_argument('--proxy',
                    help = "Proxy-configuration for HTTPS-Request in the form: http(s)://username:password@proxy:port. Please ask your system-administrator")

parser.add_argument('--debug',
                    help = "Show debugging information in case of an error",
                    action = "store_true")

parser.add_argument('--version',
                    help = "Show version and exit.",
                    action = "store_true")

parser.add_argument("-a", "--authfile",
                    help = "Name of the auth-file",
                    default = "./gisaid_uploader.authtoken")

parser.add_argument("-t", "--authtoken",
                    help = "If provided, use this authtoken, else use the auth-file")

parser.add_argument("-l", '--logfile',
                    help = "If set, all output will be logged into this file as JSON-object. If not set, all output will be printed to stdout and to './gisaid_uploader.log'")

parser.add_argument(dest = "ctx",
                    help = "Context for the operation",
                    default = "CoV")

subparsers = parser.add_subparsers(dest = "action",
                                   help = 'Command')

parser_auth = subparsers.add_parser('authenticate',
                                    help = '(Interactively) ask for user credentials, generate an authentication-token and store it in the auth-file')
parser_auth.add_argument('--cid',
                         help = "The client-id for authentication",
                         dest = "client_id")
parser_auth.add_argument('--user',
                         help = "The username for authentication")
parser_auth.add_argument('--pass',
                         help = "The password for authentication",
                         dest = "password")

parser_upl = subparsers.add_parser('upload',
                                   help = 'Batch-Upload CSV and FASTA file to the GISAID curation-zone')
parser_upl.add_argument('--csv',
                        help = "The virus metadata file formatted for GISAID Batch-Upload as CSV-File",
                        required = True)
parser_upl.add_argument('--fasta',
                        help = "The FASTA-File machting to the metadata",
                        required = True)
parser_upl.add_argument('--failedout',
                        help = "Name of an CSV-output-file that will contain all failed submissions")

parser_rev = subparsers.add_parser('revoke',
                                   help = 'Invalidate all authentication-tokens of this client for all contexts')
parser_rev.add_argument('--cid',
                         help = "All tokens of this client-id will be revoked",
                         dest = "client_id")


# helper functions and classes
client_type = "live"
def get_service_url():
    if client_type == "test":
        return GPS_SERVICE_URL_TEST
    elif client_type == "local":
        return GPS_SERVICE_URL_LOCAL
    else:
        return GPS_SERVICE_URL

proxy = None
def call_api(params, debug):
    """ call the GPS-API """
    global proxy
    body = json.dumps(params)
    try:
        r = requests.post(get_service_url(), data = body, proxies = proxy)
        time.sleep(0.1)
        return r.json()
    except requests.exceptions.ProxyError:
        if debug:
            raise
        else:
            return {"rc": "proxy_error"}
    except KeyboardInterrupt:
        raise
    except:
        if debug:
            raise
        else:
            return {"rc": "connection_error"}

def sha512_hexdigest(inp):
    hasher = hashlib.sha512()
    hasher.update(inp)
    return hasher.hexdigest()

def request_authentication_token(ctx, client_id, user, password, debug):
    """ request the authentication token from the GPS-API """

    password = password.encode("utf8")

    salt = secrets.token_urlsafe(64)
    hashed = salt + "/" + sha512_hexdigest((salt + sha512_hexdigest(password)).encode("ascii"))

    resp = call_api({"cmd": "state/auth/get_token",
                     "api": {"version": 1},
                     "ctx": ctx,
                     "client_id": client_id,
                     "login": user,
                     "hash": hashed}, debug = debug)

    return resp["rc"], resp.get("auth_token"), resp.get("valid_until")


def revoke_all_authtokens(ctx, client_id):

    resp = call_api({"cmd": "state/auth/revoke_tokens_by_client",
                     "api": {"version": 1},
                     "ctx": ctx,
                     "client_id": client_id}, debug = False)

    return resp["rc"]


def write_authentication_token_file(ctx, filename, token, debug):
    try:
        with open(filename, "rt") as file:
            tokens = json.loads(file.read())
    except:
        if debug:
            raise
        else:
            tokens = {}
    tokens[ctx] = token
    with open(filename, "w") as file:
        file.write(json.dumps(tokens))

def load_authentication_token(ctx, filename, debug):
    try:
        with open(filename, "r") as file:
            return json.loads(file.read())[ctx]
    except:
        if debug:
            raise
        else:
            return None

def parse_csv(filename):
    file = open(filename, "rt", encoding = "utf-8")
    return csv.DictReader(file, delimiter = ",", quotechar = "\"")

def parse_fasta(fn):
    seq = None
    header = None
    for row in open(fn, "rt", encoding = "utf-8"):
        row = row.strip()
        if row:
            if row[0] == ">":
                if seq:
                    yield header, "".join(seq)
                header = row[1:].lstrip()
                seq = []
            else:
                if ">" in row:
                    raise ValueError("Found '>' in sequence-data")
                seq.append(row)
    if seq:
        yield header, "".join(seq)


def split_every(n, iterable):
    iterable = iter(iterable)
    yield from iter(lambda: list(islice(iterable, n)), [])



# main handler
def handle(args):
    global client_type
    global proxy

    if args.proxy:
        proxy = {"https": args.proxy,
                 "http": args.proxy}

    if not args.logfile:
        if os.path.exists("gisaid_uploader.log"):
            os.remove("gisaid_uploader.log")

    logfile = []
    def log(code, *msg):
        if args.logfile:
            logfile.append({"code": code, "msg": " ".join(msg)})
        else:
            print(*msg)
            with open("gisaid_uploader.log", "ta") as f:
                f.write(" ".join(msg) + os.linesep)

    failed_writer = None
    failed_file = None
    def output_faulty(submission):
        if failed_writer:
            failed_writer.writerow(submission)



    if args.version:
        log("version", version)
        return 0, logfile

    # execute CLI-commands
    if args.action == "authenticate":

        # ask for params if necessary
        if not args.client_id:
            args.client_id = input("Enter Client-id: ")
        if not args.user:
            args.user = input("Enter Username:  ")
        if not args.password:
            args.password = getpass.getpass("Enter Password:  ")

        if args.client_id.startswith("TEST-"):
            client_type = "test"
        elif args.client_id.startswith("LOCAL-"):
            client_type = "local"

        # get the token
        rc, auth_token, valid_until = request_authentication_token(ctx = args.ctx,
                                                                   client_id = args.client_id,
                                                                   user = args.user,
                                                                   password = args.password,
                                                                   debug = args.debug)

        if rc == "ok":
            log("valid_until", "valid until:", time.ctime(valid_until))
            log("ok", "user authenticated")
        elif rc == "unknown_client_id":
            log("unknown_cid", "unknown client-id")
        elif rc == "wrong_credentials":
            log("no_auth", "could not authenticate user")
        else:
            log("error", "unexpected response from GPS-API: " + rc)

        # save it or report error
        if auth_token:
            write_authentication_token_file(args.ctx, args.authfile, args.client_id + "/" + auth_token, args.debug)
            return 0, logfile
        else:
            return 1, logfile

    elif args.action == "revoke":

        # get the auth-token from the command line or from the token-file
        auth_token = args.authtoken or load_authentication_token(args.ctx, args.authfile, args.debug)
        if (not auth_token or "/" not in auth_token) and (not args.client_id):
            log("invalid_params", "--authtoken not supplied or auth-file not found or supplied authtoken invalid for this context or no --cid supplied")
            return 1, logfile

        if auth_token:
            client_id, auth_token = auth_token.split("/")
        else:
            client_id = args.client_id

        if client_id.startswith("TEST-"):
            client_type = "test"
        elif client_id.startswith("LOCAL-"):
            client_type = "local"

        # revoke the token
        rc = revoke_all_authtokens(args.ctx, client_id)

        # report result
        if rc == "ok":
            write_authentication_token_file(args.ctx, args.authfile, None, args.debug)
            log("ok", "all auth-tokens sucessfully revoked")
            return 0, logfile
        elif rc == "none_found":
            log("ok", "no auth-tokens found")
            return 0, logfile
        elif resp["rc"] == "unknown_client_id":
            log("unknown_cid", "unknown client-id")
        else:
            log("error", "unexpected response from GPS-API")
            return 1, logfile

    elif args.action == "upload":

        # get the auth-token from the file or from the command line
        auth_token = args.authtoken or load_authentication_token(args.ctx, args.authfile, args.debug)
        if not auth_token or "/" not in auth_token:
            log("invalid_params", "--authtoken not supplied or auth-file not found or supplied authtoken invalid for this context")
            return 1, logfile
        if auth_token:
            client_id, auth_token = auth_token.split("/")
        else:
            client_id = args.client_id

        if client_id.startswith("TEST-"):
            client_type = "test"
        elif client_id.startswith("LOCAL-"):
            client_type = "local"

        # parse CSV
        metadata = parse_csv(args.csv)

        # prepare a CSV-Write with the same header as the input-file for the failed uploads
        if args.failedout:
            failed_file = open(args.failedout, "wt", encoding = "utf-8")
            failed_writer = csv.DictWriter(failed_file,
                                           metadata.fieldnames,
                                           delimiter = ",",
                                           quotechar = "\"",
                                           extrasaction = "ignore")
            failed_writer.writeheader()

        # parse FASTA
        try:
            sequences = {header: sequence for header, sequence in parse_fasta(args.fasta)}
        except ValueError:
            log("fasta_format_error", "upload aborded")
            return 1, logfile


        # check for completeness
        submissions = []
        missing_data = False
        for row in metadata:
            submission = dict(row)
            if submission["covv_virus_name"] not in sequences:
                log("missing_seq", "missing sequence for " + submission["covv_virus_name"])
                missing_data = True
            submission["covv_sequence"] = sequences[submission["covv_virus_name"]]
            submissions.append(submission)

        if missing_data:
            log("missing_data", "upload aborded")
            return 1, logfile


        submission_chunks = split_every(500, submissions)
        count = 0
        ok_count = 0
        for submission_chunk in submission_chunks:
            # open session
            resp = call_api({"cmd": "state/session/logon",
                             "api": {"version": 1},
                             "ctx": args.ctx,
                             "client_id": client_id,
                             "auth_token": auth_token}, debug = args.debug)
            time.sleep(0.5) # give system time to save session

            if resp["rc"] == "auth_token_invalid":
                log("invalid_token", "invalid auth-token")
                return 1, logfile
            elif resp["rc"] != "ok":
                log("error", "unexpected response from GPS-API", repr(resp))
                return 1, logfile

            sid = resp["sid"]

            # do uploads
            for submission in submission_chunk:
                submitter = submission["submitter"]
                resp = call_api({"cmd": "data/hcov-19/upload",
                                 "api": {"version": 1},
                                 "sid": sid,
                                 "ctx": args.ctx,
                                 "data": submission,
                                 "submitter": submitter}, debug = args.debug)
                if resp["rc"] == "ok":
                    ok_count += 1
                    log("epi_isl_id", "%s; %s" % (submission.get("covv_virus_name", ""), resp["accession_id"]))
                else:
                    output_faulty(submission)
                    if "validation" in resp:
                        log("validation_error", "%s; %s; %s" % (submission.get("covv_virus_name", ""), resp["rc"], json.dumps(resp["validation"])))
                    else:
                        log("upload_error", "%s; %s" % (submission.get("covv_virus_name", ""), resp["rc"]))
                count += 1

            # close session
            resp = call_api({"cmd": "state/session/logoff",
                             "api": {"version": 1},
                             "ctx": args.ctx,
                             "sid": sid}, debug = args.debug)


        log("upload_count", "submissions uploaded: %i" % ok_count)
        log("failed_count", "submissions failed: %i" % (count - ok_count))

        # close the file for the failed uploads if needed
        if failed_file:
            failed_file.close()


        return 0, logfile


if __name__ == "__main__":
    args = parser.parse_args()

    try:
        exit_code, logfile = handle(args)
    except KeyboardInterrupt:
        print("user interrupt")
        sys.exit(1)

    if args.logfile:
        with open(args.logfile, "wt") as f:
            f.write(json.dumps(logfile, indent = 4))

    sys.exit(exit_code)

