#!/usr/bin/env bash
# Run this ONCE on the VPS (as ubuntu), after the DNS A record for
# camelia.lumelio.fr → <VPS IP> has propagated.
#
#   scp vps/setup_subdomain.sh ubuntu@vps-8dd18a9f.vps.ovh.net:~
#   ssh ubuntu@vps-8dd18a9f.vps.ovh.net 'bash ~/setup_subdomain.sh'
#
# Idempotent — safe to re-run.

set -euo pipefail

DOMAIN="camelia.lumelio.fr"
DOCROOT="/home/ubuntu/camelia"
CERT_EMAIL="lumelio.pv@gmail.com"

# 1. Detect webserver
if systemctl is-active --quiet nginx; then
    WEB="nginx"
elif systemctl is-active --quiet apache2; then
    WEB="apache"
else
    echo "ERROR: neither nginx nor apache2 is running on this VPS."
    exit 1
fi
echo ">>> Detected webserver: $WEB"

# 2. Ensure PHP-FPM (nginx) or mod_php (apache) is installed
if ! command -v php >/dev/null; then
    echo ">>> Installing PHP..."
    sudo apt-get update -qq
    if [[ "$WEB" == "nginx" ]]; then
        sudo apt-get install -y php-fpm php-cli
    else
        sudo apt-get install -y libapache2-mod-php php-cli
    fi
fi

# 3. Ensure the docroot exists (deploy.sh creates it too, but just in case)
mkdir -p "$DOCROOT/data/schedules"

# 4. Write vhost + reload
if [[ "$WEB" == "nginx" ]]; then
    PHP_SOCK=$(ls /run/php/php*-fpm.sock 2>/dev/null | head -1)
    if [[ -z "$PHP_SOCK" ]]; then
        echo "ERROR: no php-fpm socket found in /run/php/"
        exit 1
    fi
    echo ">>> Writing nginx config (PHP socket: $PHP_SOCK)"
    sudo tee /etc/nginx/sites-available/$DOMAIN >/dev/null <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;
    root $DOCROOT;
    index book.php;

    location / {
        try_files \$uri \$uri/ =404;
    }

    location ~ \\.php\$ {
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:$PHP_SOCK;
    }

    # Lead data must never be directly addressable.
    location /data { deny all; return 404; }
}
EOF
    sudo ln -sfn /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/$DOMAIN
    sudo nginx -t
    sudo systemctl reload nginx
else
    echo ">>> Writing apache vhost"
    sudo tee /etc/apache2/sites-available/$DOMAIN.conf >/dev/null <<EOF
<VirtualHost *:80>
    ServerName $DOMAIN
    DocumentRoot $DOCROOT

    <Directory $DOCROOT>
        Options -Indexes +FollowSymLinks
        AllowOverride None
        Require all granted
        DirectoryIndex book.php
    </Directory>

    <Directory $DOCROOT/data>
        Require all denied
    </Directory>

    ErrorLog \${APACHE_LOG_DIR}/camelia_error.log
    CustomLog \${APACHE_LOG_DIR}/camelia_access.log combined
</VirtualHost>
EOF
    sudo a2ensite $DOMAIN
    sudo apache2ctl configtest
    sudo systemctl reload apache2
fi

# 5. TLS cert via Let's Encrypt
if ! command -v certbot >/dev/null; then
    sudo apt-get install -y certbot "python3-certbot-${WEB}"
fi
sudo certbot --$WEB -d $DOMAIN \
    --non-interactive --agree-tos -m "$CERT_EMAIL" --redirect

echo
echo ">>> Setup complete."
echo ">>> Test:  curl -s 'https://$DOMAIN/book.php?t=baadbeef&s=2026-05-14_morning' | head -20"
echo ">>> Should return our bilingual 'Lien expiré / Link expired' page."
