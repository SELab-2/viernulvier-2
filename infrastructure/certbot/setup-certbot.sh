#!/bin/bash

# Initial SSL certificate setup using Let's Encrypt and Certbot.
# Run this ONCE on the server before the first deployment.
# After this, the certbot container handles automatic renewal.
#
# Usage (from repository root):
#   bash infrastructure/certbot/setup-certbot.sh <domain> <email>

set -e

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <domain> <email>"
    exit 1
fi

DOMAIN=$1
EMAIL=$2

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/../docker-compose.prod.yml"
RSA_KEY_SIZE=4096

export DOMAIN

echo "Setting up SSL for $DOMAIN..."

docker compose -f "$COMPOSE_FILE" run --rm --entrypoint "\
    sh -c \"mkdir -p /etc/letsencrypt && \
    wget -q -O /etc/letsencrypt/options-ssl-nginx.conf \
        https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf && \
    wget -q -O /etc/letsencrypt/ssl-dhparams.pem \
        https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem\"" \
    certbot

docker compose -f "$COMPOSE_FILE" run --rm --entrypoint "\
    openssl req -x509 -nodes -newkey rsa:$RSA_KEY_SIZE -days 1 \
        -keyout '/etc/letsencrypt/live/$DOMAIN/privkey.pem' \
        -out '/etc/letsencrypt/live/$DOMAIN/fullchain.pem' \
        -subj '/CN=localhost'" \
    certbot

docker compose -f "$COMPOSE_FILE" up --force-recreate -d nginx

docker compose -f "$COMPOSE_FILE" run --rm --entrypoint "\
    rm -rf /etc/letsencrypt/live/$DOMAIN && \
    rm -rf /etc/letsencrypt/archive/$DOMAIN && \
    rm -rf /etc/letsencrypt/renewal/$DOMAIN.conf" \
    certbot

docker compose -f "$COMPOSE_FILE" run --rm --entrypoint "\
    certbot certonly --webroot -w /var/www/certbot \
        --email $EMAIL \
        -d $DOMAIN \
        --rsa-key-size $RSA_KEY_SIZE \
        --agree-tos \
        --no-eff-email \
        --force-renewal" \
    certbot

docker compose -f "$COMPOSE_FILE" exec nginx nginx -s reload

echo "SSL certificate for $DOMAIN has been set up successfully."
