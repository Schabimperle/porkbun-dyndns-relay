# Porkbun DynDNS Relay

A lightweight Flask-based application for dynamically updating DNS A and AAAA records on Porkbun. The application listens for HTTP GET requests to update DNS records based on provided parameters.

## Features

- **Immediate update**: No delay when used with Fritz!Box DynDNS feature compared to simple polling solutions.
- **IPv4 and IPv6 Support**: Updates both A and AAAA records.
- **Automatic Record Management**: Creates new records or updates existing ones.

## Requirements

- Porkbun API key and secret key
- Python 3.9 or later
- Docker (for containerized deployment)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Schabimperle/porkbun-dyndxns-relay.git
   cd porkbun-dyndns-relay
   ```

2. Build the Docker image:
   ```bash
   docker build -t porkbun-dyndns-relay .
   ```

3. Run the Docker container:
   ```bash
   docker run -d -p 5454:5454 porkbun-dyndns-relay
   ```

## API Endpoints

### Update DNS Record

**Endpoint:** `/update-dns-record`

**Method:** `GET`

**Query Parameters:**

| Parameter    | Description                         | Required |
|--------------|-------------------------------------|----------|
| `apiKey`     | Your Porkbun API key                | Yes      |
| `secretKey`  | Your Porkbun secret API key         | Yes      |
| `domain`     | The full domain name to update      | Yes      |
| `ipv4address`| IPv4 address for the A record       | Optional |
| `ipv6address`| IPv6 address for the AAAA record    | Optional |

**Response:**
- `200 OK`: DNS records updated or created successfully.
- `400 Bad Request`: Missing or invalid parameters.
- `500 Internal Server Error`: Failed to retrieve or update DNS records.

**Example Request:**
```bash
curl "http://<server_ip>:5454/update-dns-record?apiKey=your_api_key&secretKey=your_secret_key&domain=sub.example.com&ipv4address=192.0.2.1&ipv6address=2001:db8::1"
```

### Example Configuration for Fritz!Box Dynamic DNS

For configuring a Fritz!Box to use this service as a dynamic DNS provider, set the update URL as follows. Just replace the `<server_ip>`, the rest will be replaced by the Fritz!Box itself:
```text
http://<server_ip>:5454/update-dns-record?apiKey=<username>&secretKey=<passwd>&domain=<domain>&ipv4address=<ipaddr>&ipv6address=<ip6addr>
```
In the Fritz!Box configuration form:
- **Update URL**: Use the URL format above.
- **Username**: Enter your Porkbun API key.
- **Password**: Enter your Porkbun secret API key.
- **Domain**: Enter the full domain name to update.

## Deployment Notes

- Ensure the container has network access to Porkbun's API (`https://api.porkbun.com`).
- Bind the container to the desired port (default: `5454`).
- For IPv6 support, ensure your hosting environment supports IPv6 connectivity.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.