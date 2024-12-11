import logging
import requests
import signal
import sys
import tldextract
from flask import Flask, request, jsonify
from threading import Thread

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants and configuration
PORKBUN_API_URL = "https://api.porkbun.com/api/json/v3"

def parse_subdomain(url):
    extracted = tldextract.extract(url)
    return extracted

# Function to retrieve DNS records
def retrieve_dns_records(domain_name, api_key, secret_key):
    try:
        response = requests.post(f"{PORKBUN_API_URL}/dns/retrieve/{domain_name}", json={
            "apikey": api_key,
            "secretapikey": secret_key
        })
        response.raise_for_status()
        return response.json().get("records", [])
    except requests.RequestException as e:
        logging.error(f"Failed to retrieve DNS records: {e}")
        return None

# Function to update an existing A or AAAA record
def update_record(api_key, secret_key, domain_name, subdomain, ip_address, record_id, record_type):
    payload = {
        "apikey": api_key,
        "secretapikey": secret_key,
        "name": subdomain,
        "type": record_type,
        "content": ip_address,
        "ttl": 600
    }
    try:
        response = requests.post(f"{PORKBUN_API_URL}/dns/edit/{domain_name}/{record_id}", json=payload)
        response.raise_for_status()
        logging.info(f"{record_type} record updated successfully.")
        return {"success": f"{record_type} record updated successfully"}
    except requests.RequestException as e:
        logging.error(f"Failed to update {record_type} record: {e}")
        return {"error": f"Failed to update {record_type} record"}

# Function to create a new A or AAAA record
def create_record(api_key, secret_key, domain_name, subdomain, ip_address, record_type):
    payload = {
        "apikey": api_key,
        "secretapikey": secret_key,
        "name": subdomain,
        "type": record_type,
        "content": ip_address,
        "ttl": 600
    }
    try:
        response = requests.post(f"{PORKBUN_API_URL}/dns/create/{domain_name}", json=payload)
        response.raise_for_status()
        logging.info(f"{record_type} record created successfully.")
        return {"success": f"{record_type} record created successfully"}
    except requests.RequestException as e:
        logging.error(f"Failed to create {record_type} record: {e}")
        return {"error": f"Failed to create {record_type} record"}

@app.route('/update-dns-record', methods=['GET'])
def handle_update_dns_record():
    api_key = request.args.get('apiKey')
    if not api_key:
        logging.warning('API key not provided in request.')
        return jsonify({'error': 'API key not provided'}), 400

    secret_key = request.args.get('secretKey')
    if not secret_key:
        logging.warning('Secret key not provided in request.')
        return jsonify({'error': 'Secret key not provided'}), 400

    domain = request.args.get('domain')
    if not domain:
        logging.warning('Domain not provided in request.')
        return jsonify({'error': 'Domain not provided'}), 400

    ipv4address = request.args.get('ipv4address')
    ipv6address = request.args.get('ipv6address')

    if not ipv4address and not ipv6address:
        logging.warning('No IP address provided in request.')
        return jsonify({'error': 'No IP address provided'}), 400

    extracted = parse_subdomain(domain)
    domain_name = f"{extracted.domain}.{extracted.suffix}"
    subdomain = extracted.subdomain

    # Retrieve existing DNS records
    records = retrieve_dns_records(domain_name, api_key, secret_key)
    if records is None:
        return jsonify({'error': 'Failed to retrieve DNS records'}), 500

    responses = []

    # Handle A and AAAA records
    for ip_address, record_type in [(ipv4address, "A"), (ipv6address, "AAAA")]:
        if ip_address:
            record_id = None
            for record in records:
                if record["type"] == record_type and record["name"] == domain:
                    record_id = record["id"]
                    break

            if record_id:
                logging.info(f"{record_type} record for {subdomain}.{domain_name} exists. Updating it.")
                responses.append(update_record(api_key, secret_key, domain_name, subdomain, ip_address, record_id, record_type))
            else:
                logging.info(f"{record_type} record for {subdomain}.{domain_name} does not exist. Creating it.")
                responses.append(create_record(api_key, secret_key, domain_name, subdomain, ip_address, record_type))

    return jsonify({'responses': responses}), 200

# Graceful shutdown handler
def graceful_shutdown(signal_number, frame):
    logging.info('Received exit signal. Shutting down gracefully...')
    func = request.environ.get('werkzeug.server.shutdown')
    if func:
        func()
    logging.info('Server has shut down.')
    sys.exit(0)

# Register signals for graceful shutdown
signal.signal(signal.SIGINT, graceful_shutdown)  # Handle Ctrl+C
signal.signal(signal.SIGTERM, graceful_shutdown)  # Handle termination signal

if __name__ == '__main__':
    # Start the Flask app in a separate thread for proper shutdown handling
    def run_app():
        app.run(host='::', port=5454)  # Bind to IPv6 and IPv4

    # Start Flask in a separate thread
    flask_thread = Thread(target=run_app)
    flask_thread.start()

    # Wait for Flask thread to complete (or receive a shutdown signal)
    flask_thread.join()
