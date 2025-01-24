import logging
from flask import Flask, request, jsonify
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import tldextract

# Flask app initialization
app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants and configuration
PORKBUN_API_URL = "https://api.porkbun.com/api/json/v3"

# Configure retries for requests
session = requests.Session()
retry = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504],
    raise_on_status=False
)
adapter = HTTPAdapter(max_retries=retry)
session.mount("https://", adapter)
session.mount("http://", adapter)

def parse_subdomain(url):
    extracted = tldextract.extract(url)
    return extracted

# Function to retrieve DNS records
def retrieve_dns_records(domain_name, api_key, secret_key):
    try:
        response = session.post(f"{PORKBUN_API_URL}/dns/retrieve/{domain_name}", json={
            "apikey": api_key,
            "secretapikey": secret_key
        }, timeout=10)
        response.raise_for_status()
        return response.json().get("records", [])
    except requests.exceptions.SSLError as e:
        logging.error(f"SSL error when retrieving DNS records: {e}")
        return None
    except requests.RequestException as e:
        logging.error(f"Failed to retrieve DNS records: {e}")
        return None

# Function to update or create records (shared logic)
def manage_record(api_key, secret_key, domain_name, subdomain, ip_address, record_type, record_id=None):
    url = f"{PORKBUN_API_URL}/dns/{'edit' if record_id else 'create'}/{domain_name}/{record_id or ''}"
    payload = {
        "apikey": api_key,
        "secretapikey": secret_key,
        "name": subdomain,
        "type": record_type,
        "content": ip_address,
        "ttl": 600
    }
    try:
        response = session.post(url, json=payload, timeout=10)
        response.raise_for_status()
        action = "updated" if record_id else "created"
        logging.info(f"{record_type} record {action} successfully.")
        return {"success": f"{record_type} record {action} successfully"}
    except requests.RequestException as e:
        logging.error(f"Failed to {action} {record_type} record: {e}")
        return {"error": f"Failed to {action} {record_type} record"}

@app.route('/update-dns-record', methods=['GET'])
def handle_update_dns_record():
    api_key = request.args.get('apiKey')
    secret_key = request.args.get('secretKey')
    domain = request.args.get('domain')
    ipv4address = request.args.get('ipv4address')
    ipv6address = request.args.get('ipv6address')

    if not all([api_key, secret_key, domain]):
        logging.warning('Required parameters missing in request.')
        return jsonify({'error': 'Missing required parameters'}), 400

    extracted = parse_subdomain(domain)
    domain_name = f"{extracted.domain}.{extracted.suffix}"
    subdomain = extracted.subdomain

    records = retrieve_dns_records(domain_name, api_key, secret_key)
    if records is None:
        return jsonify({'error': 'Failed to retrieve DNS records'}), 500

    responses = []
    for ip_address, record_type in [(ipv4address, "A"), (ipv6address, "AAAA")]:
        if ip_address:
            record_id = next((r["id"] for r in records if r["type"] == record_type and r["name"] == domain), None)
            responses.append(manage_record(api_key, secret_key, domain_name, subdomain, ip_address, record_type, record_id))

    return jsonify({'responses': responses}), 200

if __name__ == '__main__':
    logging.info('This script should be run with Gunicorn, not directly.')
