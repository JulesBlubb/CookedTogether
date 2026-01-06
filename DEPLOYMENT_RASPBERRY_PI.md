# Raspberry Pi Deployment Guide - Cooked Together

## Making Your Recipe App Accessible from Anywhere

This guide shows how to deploy on a Raspberry Pi at home and make it accessible to family members on different networks (like your mother accessing from her home).

---

## Table of Contents
1. [Raspberry Pi Setup](#raspberry-pi-setup)
2. [Network Access Solutions](#network-access-solutions)
3. [Option A: Cloudflare Tunnel (Recommended)](#option-a-cloudflare-tunnel-recommended)
4. [Option B: Tailscale VPN](#option-b-tailscale-vpn)
5. [Option C: Port Forwarding + DynDNS](#option-c-port-forwarding--dyndns)
6. [Security Considerations](#security-considerations)

---

## Raspberry Pi Setup

### Initial Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3-pip python3-venv nginx git
sudo apt install -y tesseract-ocr tesseract-ocr-deu  # For OCR

# Create app directory
sudo mkdir -p /opt/cookedtogether
sudo chown pi:pi /opt/cookedtogether
cd /opt/cookedtogether

# Clone your repository
git clone https://github.com/your-username/CookedTogether.git app
cd app/recipe_app

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn

# Generate secure tokens
python3 -c 'import secrets; print("SECRET_KEY=" + secrets.token_hex(32))' > tokens.txt
python3 -c 'import secrets; print("RECIPE_AUTH_TOKEN=" + secrets.token_urlsafe(32))' >> tokens.txt
cat tokens.txt  # Save these!

# Create .env file
cp .env.example .env
nano .env  # Paste your tokens

# Create necessary directories
mkdir -p uploads logs
chmod 755 uploads

# Initialize database
python3 -c "from app import app, db; app.app_context().push(); db.create_all()"

# Test it works locally
gunicorn --bind 0.0.0.0:8000 app:app
# Visit http://raspberrypi.local:8000 from another device on your network
```

### Create Systemd Service

Create `/etc/systemd/system/cookedtogether.service`:

```bash
sudo nano /etc/systemd/system/cookedtogether.service
```

Paste this content:

```ini
[Unit]
Description=Cooked Together Recipe App
After=network.target

[Service]
Type=notify
User=pi
Group=www-data
WorkingDirectory=/opt/cookedtogether/app/recipe_app
Environment="PATH=/opt/cookedtogether/app/recipe_app/venv/bin"
EnvironmentFile=/opt/cookedtogether/app/recipe_app/.env

ExecStart=/opt/cookedtogether/app/recipe_app/venv/bin/gunicorn \
    --config gunicorn_config.py \
    --bind 127.0.0.1:8000 \
    app:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable cookedtogether
sudo systemctl start cookedtogether
sudo systemctl status cookedtogether
```

### Configure Nginx (Local)

```bash
sudo nano /etc/nginx/sites-available/cookedtogether
```

```nginx
server {
    listen 80;
    server_name _;

    client_max_body_size 16M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /opt/cookedtogether/app/recipe_app/static;
        expires 30d;
    }

    location /uploads {
        alias /opt/cookedtogether/app/recipe_app/uploads;
        expires 7d;
    }
}
```

Enable:

```bash
sudo ln -s /etc/nginx/sites-available/cookedtogether /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Remove default site
sudo nginx -t
sudo systemctl restart nginx
```

**Now it works on your local network!** Test from your phone: `http://raspberrypi.local`

---

## Network Access Solutions

Your mother needs to access your Pi from her home network. Here are 3 solutions:

| Solution | Difficulty | Cost | Security | Best For |
|----------|-----------|------|----------|----------|
| **Cloudflare Tunnel** | Easy | Free | Excellent | Everyone (Recommended) |
| **Tailscale VPN** | Easy | Free | Excellent | Tech-savvy families |
| **Port Forwarding + DynDNS** | Hard | $5-15/year | Moderate | DIY enthusiasts |

---

## Option A: Cloudflare Tunnel (Recommended)

**Best solution**: Free, secure, no port forwarding, works behind CGNAT/double NAT.

### How it Works
- Creates a secure tunnel from your Pi to Cloudflare's network
- Your mother accesses `recipes.yourdomain.com`
- Cloudflare routes traffic through the tunnel to your Pi
- No need to expose your home IP or open ports!

### Prerequisites
- A domain name (can get free at Freenom or cheap at Namecheap ~$10/year)
- Free Cloudflare account

### Step 1: Install Cloudflared on Raspberry Pi

```bash
# Download cloudflared (ARM architecture)
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64
sudo mv cloudflared-linux-arm64 /usr/local/bin/cloudflared
sudo chmod +x /usr/local/bin/cloudflared

# Verify installation
cloudflared --version
```

### Step 2: Set Up Domain on Cloudflare

1. **Get a domain** (if you don't have one):
   - Cheap option: Namecheap, Porkbun (~$10/year for .com)
   - Free option: Freenom (.tk, .ml domains)

2. **Add domain to Cloudflare**:
   - Sign up at [cloudflare.com](https://cloudflare.com)
   - Add your domain
   - Update nameservers at your registrar to Cloudflare's

### Step 3: Authenticate Cloudflared

```bash
cloudflared tunnel login
```

This opens a browser - login to Cloudflare and authorize.

### Step 4: Create Tunnel

```bash
# Create tunnel
cloudflared tunnel create cookedtogether

# Note the tunnel ID (shown in output)
# Example: Created tunnel cookedtogether with id: abc123-def456-ghi789

# Create config file
sudo mkdir -p /etc/cloudflared
sudo nano /etc/cloudflared/config.yml
```

Paste this config (replace `TUNNEL-ID` and `yourdomain.com`):

```yaml
tunnel: TUNNEL-ID
credentials-file: /home/pi/.cloudflared/TUNNEL-ID.json

ingress:
  - hostname: recipes.yourdomain.com
    service: http://localhost:80
  - service: http_status:404
```

### Step 5: Create DNS Record

```bash
# Route your subdomain to the tunnel
cloudflared tunnel route dns cookedtogether recipes.yourdomain.com
```

### Step 6: Run Tunnel as Service

```bash
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
sudo systemctl status cloudflared
```

**Done!** Your mother can now access:
```
https://recipes.yourdomain.com
```

HTTPS is automatic with Cloudflare! 🎉

### Testing

From your mother's house:
```
https://recipes.yourdomain.com
```

She should see your recipe app. To add recipes:
1. Go to `https://recipes.yourdomain.com/add_recipe`
2. Enter the auth token (share via password manager)
3. Create recipes!

---

## Option B: Tailscale VPN

**Best for**: Small groups who don't mind installing an app.

### How it Works
- Creates a private VPN network
- Everyone installs Tailscale app
- Access Pi via internal IP (e.g., `100.64.0.5`)
- Secure, encrypted, no public exposure

### Setup

1. **Sign up at [tailscale.com](https://tailscale.com)** (free for personal use)

2. **Install on Raspberry Pi**:
   ```bash
   curl -fsSL https://tailscale.com/install.sh | sh
   sudo tailscale up
   ```

3. **Install on your mother's device**:
   - Download Tailscale app (Windows/Mac/iOS/Android)
   - Sign in with same account
   - Accept connection

4. **Access the app**:
   ```bash
   # On Pi, find your Tailscale IP
   tailscale ip -4
   # Example output: 100.64.0.5
   ```

   Your mother visits: `http://100.64.0.5` (or assign a hostname)

### Pros & Cons

✅ **Pros:**
- Very secure (encrypted VPN)
- No port forwarding
- Works behind any NAT/firewall
- Can access other services too

❌ **Cons:**
- Requires app installation on all devices
- IP address instead of nice domain name
- Less convenient for non-tech users

---

## Option C: Port Forwarding + Dynamic DNS

**Not recommended** for most users (less secure, more complex).

### How it Works
- Forward port 80/443 on your router to Pi
- Use DynDNS to get a domain pointing to your home IP
- Your mother accesses `recipes.yourname.dyndns.org`

### Prerequisites
- Router admin access
- ISP must provide a public IP (not CGNAT)
- Dynamic DNS service account

### Step 1: Dynamic DNS Setup

Choose a provider:
- **DuckDNS** (free, easy)
- **No-IP** (free tier available)
- **Dynu** (free tier available)

**Example with DuckDNS:**

```bash
# Sign up at duckdns.org
# Create subdomain: yourname.duckdns.org

# Install DuckDNS updater on Pi
mkdir ~/duckdns
cd ~/duckdns
nano duck.sh
```

```bash
#!/bin/bash
echo url="https://www.duckdns.org/update?domains=yourname&token=YOUR-TOKEN&ip=" | curl -k -o ~/duckdns/duck.log -K -
```

```bash
chmod +x duck.sh

# Test it
./duck.sh
cat duck.log  # Should say "OK"

# Auto-update every 5 minutes
crontab -e
# Add: */5 * * * * ~/duckdns/duck.sh >/dev/null 2>&1
```

### Step 2: Port Forwarding

1. **Find Pi's local IP**:
   ```bash
   hostname -I
   # Example: 192.168.1.100
   ```

2. **Access your router** (usually `192.168.1.1` or `192.168.0.1`)

3. **Forward ports**:
   - External Port: 80 → Internal IP: 192.168.1.100, Port: 80
   - External Port: 443 → Internal IP: 192.168.1.100, Port: 443

4. **Set static IP for Pi** (in router DHCP settings)

### Step 3: Get HTTPS Certificate

```bash
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourname.duckdns.org
```

### Step 4: Update Nginx Config

```bash
sudo nano /etc/nginx/sites-available/cookedtogether
```

```nginx
server {
    listen 80;
    server_name yourname.duckdns.org;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourname.duckdns.org;

    ssl_certificate /etc/letsencrypt/live/yourname.duckdns.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourname.duckdns.org/privkey.pem;

    client_max_body_size 16M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /opt/cookedtogether/app/recipe_app/static;
    }

    location /uploads {
        alias /opt/cookedtogether/app/recipe_app/uploads;
    }
}
```

```bash
sudo nginx -t
sudo systemctl restart nginx
```

**Access**: `https://yourname.duckdns.org`

### ⚠️ Security Warnings

- Your home IP is exposed publicly
- Pi must be kept updated (security patches)
- Use strong passwords everywhere
- Consider fail2ban to block attackers
- Monitor logs regularly

---

## Security Considerations

### For All Solutions

1. **Strong Authentication Token**:
   ```bash
   # Generate a very strong token
   python3 -c 'import secrets; print(secrets.token_urlsafe(48))'
   ```

2. **Keep Pi Updated**:
   ```bash
   # Weekly updates
   sudo apt update && sudo apt upgrade -y
   ```

3. **Firewall** (if using port forwarding):
   ```bash
   sudo apt install ufw
   sudo ufw allow 22  # SSH
   sudo ufw allow 80  # HTTP
   sudo ufw allow 443  # HTTPS
   sudo ufw enable
   ```

4. **Monitor Access**:
   ```bash
   # Check who's accessing
   sudo tail -f /var/log/nginx/access.log

   # Check for errors
   sudo journalctl -u cookedtogether -f
   ```

5. **Database Backups**:
   ```bash
   # Daily backup script
   cat > /home/pi/backup.sh <<'EOF'
#!/bin/bash
BACKUP_DIR="/home/pi/backups"
mkdir -p $BACKUP_DIR
cp /opt/cookedtogether/app/recipe_app/database.db \
   $BACKUP_DIR/database_$(date +%Y%m%d).db
find $BACKUP_DIR -name "database_*.db" -mtime +30 -delete
EOF

   chmod +x /home/pi/backup.sh

   # Add to crontab
   crontab -e
   # Add: 0 2 * * * /home/pi/backup.sh
   ```

---

## Sharing Access with Your Mother

### Step 1: Send Her the URL

**Via Cloudflare Tunnel:**
```
Hi Mom! 👋

You can now access our family recipe book at:
https://recipes.yourdomain.com

Save this link as a bookmark!
```

**Via Tailscale:**
```
Hi Mom! 👋

1. Install Tailscale app: https://tailscale.com/download
2. Sign in with this account: [share account]
3. Visit: http://100.64.0.5
```

### Step 2: Share the Auth Token Securely

**Recommended: Password Manager**

1. Store token in 1Password/Bitwarden
2. Share vault with your mother
3. She accesses token from her password manager app

**Alternative: Secure Message**

```
To add recipes, you'll need this authentication token.

Save it somewhere safe (password manager recommended):

RECIPE_AUTH_TOKEN: [paste token here]

How to use:
1. Go to https://recipes.yourdomain.com/add_recipe
2. Paste the token in the "Authentication Token" field
3. Fill in recipe details
4. Upload photo (optional)
5. Submit!
```

### Step 3: Quick Tutorial

Create a simple guide for your mother:

```
📖 How to Add a Recipe

1. Go to: https://recipes.yourdomain.com/add_recipe

2. Paste your authentication token in the first field

3. Fill in:
   - Recipe Title (e.g., "Oma's Apple Cake")
   - Portions (e.g., 8)
   - Cooking time
   - Ingredients (one per line)
   - Instructions

4. Add photo (optional):
   - Take photo of recipe or dish
   - Upload from your device

5. Click "Rezept speichern" (Save Recipe)

6. Done! Everyone can now see your recipe!
```

---

## Troubleshooting

### Can't access from external network

**Cloudflare Tunnel:**
```bash
# Check tunnel status
sudo systemctl status cloudflared

# Check logs
sudo journalctl -u cloudflared -n 50

# Restart tunnel
sudo systemctl restart cloudflared
```

**Port Forwarding:**
```bash
# Test if port is open from outside
# Use https://www.yougetsignal.com/tools/open-ports/
# Check ports 80 and 443
```

### Pi crashes or runs slow

```bash
# Check memory
free -h

# Check disk space
df -h

# Reduce Gunicorn workers if low on RAM
nano /opt/cookedtogether/app/recipe_app/gunicorn_config.py
# Change: workers = 2  # Instead of 4
```

### Database errors

```bash
# Backup current database
cp database.db database_backup.db

# Reinitialize
python3 -c "from app import app, db; app.app_context().push(); db.create_all()"
```

---

## Performance Tips for Raspberry Pi

```python
# Edit gunicorn_config.py for lower resource usage
workers = 2  # Reduce from 4
worker_class = "sync"
max_requests = 100  # Restart workers more often
timeout = 60
```

---

## Complete Setup Script

Run this for a full automated setup:

```bash
#!/bin/bash
# Save as: setup-pi.sh

set -e

echo "🍓 Setting up Cooked Together on Raspberry Pi..."

# Update system
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv nginx git tesseract-ocr tesseract-ocr-deu

# Setup app
sudo mkdir -p /opt/cookedtogether
sudo chown pi:pi /opt/cookedtogether
cd /opt/cookedtogether

# Clone repo (replace with your URL)
git clone https://github.com/your-username/CookedTogether.git app
cd app/recipe_app

# Python setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# Generate tokens
echo "🔐 Your secure tokens:"
python3 -c 'import secrets; print("SECRET_KEY=" + secrets.token_hex(32))'
python3 -c 'import secrets; print("RECIPE_AUTH_TOKEN=" + secrets.token_urlsafe(32))'
echo ""
echo "⚠️  SAVE THESE TOKENS! Press Enter when done..."
read

# Create .env (you'll need to add tokens manually)
cp .env.example .env
nano .env

# Setup directories
mkdir -p uploads logs
chmod 755 uploads

# Initialize database
python3 -c "from app import app, db; app.app_context().push(); db.create_all()"

echo "✅ App setup complete!"
echo "📋 Next steps:"
echo "1. Configure systemd service (see guide)"
echo "2. Configure nginx (see guide)"
echo "3. Choose network solution (Cloudflare Tunnel recommended)"
```

---

## Recommendation for Your Use Case

**Best Solution: Cloudflare Tunnel**

Why:
- ✅ Free
- ✅ No port forwarding (safer)
- ✅ Works with any ISP/NAT setup
- ✅ Automatic HTTPS
- ✅ Easy for your mother (just a URL)
- ✅ No app installation needed
- ✅ Professional domain name

**Your mother just needs:**
1. The URL: `https://recipes.yourdomain.com`
2. The auth token (from password manager)
3. That's it!

---

## Questions?

- Cloudflare Tunnel not working? Check `sudo systemctl status cloudflared`
- Can't access locally? Check `sudo systemctl status cookedtogether nginx`
- Database issues? Restore from backup: `cp database_backup.db database.db`

**Need help?** Check the logs:
```bash
sudo journalctl -u cookedtogether -n 50
sudo tail -f /var/log/nginx/error.log
```
