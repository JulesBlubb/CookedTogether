# Raspberry Pi Quick Start Guide

## 🚀 Get Your Recipe App Online in 1 Hour

This is the **fastest path** to get your recipe app running on a Raspberry Pi and accessible to your mother from anywhere.

---

## What You Need

- ✅ Raspberry Pi (any model, 3B+ or newer recommended)
- ✅ SD card with Raspberry Pi OS installed
- ✅ Internet connection
- ✅ Domain name ($10/year) OR free DuckDNS account
- ✅ Your GitHub repository cloned

---

## Part 1: Setup Pi (20 minutes)

### 1. Copy & Run This Script

SSH into your Pi and run:

```bash
# Download and run the setup script
curl -O https://raw.githubusercontent.com/your-repo/main/setup-pi.sh
chmod +x setup-pi.sh
./setup-pi.sh
```

**Or manually:**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3-pip python3-venv nginx git tesseract-ocr tesseract-ocr-deu

# Clone your repo
sudo mkdir -p /opt/cookedtogether
sudo chown pi:pi /opt/cookedtogether
cd /opt/cookedtogether
git clone https://github.com/YOUR-USERNAME/CookedTogether.git app
cd app/recipe_app

# Setup Python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# Generate tokens
echo "🔐 Save these tokens:"
python3 -c 'import secrets; print("SECRET_KEY=" + secrets.token_hex(32))'
python3 -c 'import secrets; print("RECIPE_AUTH_TOKEN=" + secrets.token_urlsafe(32))'

# Create .env file
cp .env.example .env
nano .env  # Paste your tokens here

# Create directories
mkdir -p uploads logs
chmod 755 uploads

# Initialize database
python3 -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### 2. Create Systemd Service

```bash
sudo nano /etc/systemd/system/cookedtogether.service
```

Paste:

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
ExecStart=/opt/cookedtogether/app/recipe_app/venv/bin/gunicorn --config gunicorn_config.py --bind 127.0.0.1:8000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable cookedtogether
sudo systemctl start cookedtogether
sudo systemctl status cookedtogether  # Should say "active (running)"
```

### 3. Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/cookedtogether
```

Paste:

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
    }

    location /static {
        alias /opt/cookedtogether/app/recipe_app/static;
    }

    location /uploads {
        alias /opt/cookedtogether/app/recipe_app/uploads;
    }
}
```

Enable:

```bash
sudo ln -s /etc/nginx/sites-available/cookedtogether /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

**Test:** Visit `http://raspberrypi.local` from another device on your network. You should see your recipe app! ✅

---

## Part 2: Make It Accessible from Internet (30 minutes)

Choose **ONE** option:

### Option A: Cloudflare Tunnel (⭐ RECOMMENDED)

**Prerequisites:**
- Domain name (e.g., yourname.com) - $10/year from Namecheap/Porkbun
- Free Cloudflare account

**Steps:**

1. **Install cloudflared:**

```bash
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64
sudo mv cloudflared-linux-arm64 /usr/local/bin/cloudflared
sudo chmod +x /usr/local/bin/cloudflared
```

2. **Login to Cloudflare:**

```bash
cloudflared tunnel login
# Opens browser - login and authorize
```

3. **Create tunnel:**

```bash
cloudflared tunnel create cookedtogether
# Note the tunnel ID shown (e.g., abc123-def456)
```

4. **Configure tunnel:**

```bash
sudo mkdir -p /etc/cloudflared
sudo nano /etc/cloudflared/config.yml
```

Paste (replace TUNNEL-ID and domain):

```yaml
tunnel: <TUNNEL-ID>
credentials-file: /home/pi/.cloudflared/<TUNNEL-ID>.json

ingress:
  - hostname: recipes.yourname.com
    service: http://localhost:80
  - service: http_status:404
```

5. **Route DNS:**

```bash
cloudflared tunnel route dns cookedtogether recipes.yourname.com
```

6. **Start tunnel:**

```bash
sudo cloudflared service install
sudo systemctl start cloudflared
sudo systemctl status cloudflared
```

**Done!** Your app is now at: `https://recipes.yourname.com` 🎉

---

### Option B: Tailscale VPN (Easy, No Domain Needed)

1. **Install on Pi:**

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

2. **Install on your mother's devices:**
   - Download from https://tailscale.com/download
   - Sign in with same account

3. **Get Pi's Tailscale IP:**

```bash
tailscale ip -4
# Example: 100.64.0.5
```

4. **Share with mother:**
   - She visits: `http://100.64.0.5`

---

### Option C: DuckDNS (Free, No Domain Purchase)

1. **Sign up at [DuckDNS.org](https://www.duckdns.org)**
   - Create subdomain: `yourname.duckdns.org`

2. **Install updater:**

```bash
mkdir ~/duckdns
cd ~/duckdns
nano duck.sh
```

Paste (replace TOKEN):

```bash
#!/bin/bash
echo url="https://www.duckdns.org/update?domains=yourname&token=YOUR-TOKEN&ip=" | curl -k -o ~/duckdns/duck.log -K -
```

```bash
chmod +x duck.sh
./duck.sh  # Test it
cat duck.log  # Should say "OK"

# Auto-update every 5 minutes
crontab -e
# Add: */5 * * * * ~/duckdns/duck.sh >/dev/null 2>&1
```

3. **Port forward on your router:**
   - Forward port 80 → Pi's IP (e.g., 192.168.1.100)
   - Forward port 443 → Pi's IP

4. **Get SSL certificate:**

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourname.duckdns.org
```

**Done!** App at: `https://yourname.duckdns.org`

---

## Part 3: Share with Your Mother (5 minutes)

### Send Her the Info

**Email Template:**

```
Subject: Family Recipe Book is Online! 🍳

Hi Mom!

I've set up our family recipe book. You can now access it online:

🌐 Website: https://recipes.yourname.com
   (Bookmark this!)

To ADD recipes:
1. Click "Neues Rezept" (New Recipe)
2. Enter the authentication token: <PASTE-TOKEN-HERE>
3. Fill in the recipe details
4. Upload a photo (optional)
5. Click "Rezept speichern" (Save)

The token is also saved in our family 1Password vault under "Recipe App Token"

Try it out with one of your favorite recipes! 😊

Love,
Juliane

---

Need help? Call me!
```

### Better: Use Password Manager

1. **Store token in 1Password/Bitwarden:**
   ```
   Title: Family Recipe App - Auth Token
   Username: (empty)
   Password: <YOUR-RECIPE_AUTH_TOKEN>
   Website: https://recipes.yourname.com/add_recipe
   ```

2. **Share vault with mother**

3. **She uses it:**
   - Go to website
   - Copy token from password manager
   - Paste and add recipe!

---

## Testing Checklist

- [ ] App works on local network: `http://raspberrypi.local` ✅
- [ ] App works from internet: `https://recipes.yourname.com` ✅
- [ ] Test from phone (mobile data, not WiFi) ✅
- [ ] Can view recipes without token ✅
- [ ] `/add_recipe` requires token ✅
- [ ] Creating recipe with token works ✅
- [ ] Image upload works ✅
- [ ] Portion scaling works ✅
- [ ] Translation works ✅
- [ ] Your mother can access from her house ✅

---

## Maintenance

### Weekly: Update Pi

```bash
sudo apt update && sudo apt upgrade -y
sudo systemctl restart cookedtogether
```

### Daily: Automatic Database Backup

```bash
# Create backup script
cat > /home/pi/backup.sh <<'EOF'
#!/bin/bash
BACKUP_DIR="/home/pi/backups"
mkdir -p $BACKUP_DIR
cp /opt/cookedtogether/app/recipe_app/database.db $BACKUP_DIR/database_$(date +%Y%m%d).db
find $BACKUP_DIR -name "database_*.db" -mtime +30 -delete
EOF

chmod +x /home/pi/backup.sh

# Run daily at 2 AM
crontab -e
# Add: 0 2 * * * /home/pi/backup.sh
```

### Check Logs

```bash
# Application logs
sudo journalctl -u cookedtogether -n 50

# Nginx logs
sudo tail -f /var/log/nginx/access.log

# Cloudflare tunnel logs (if using)
sudo journalctl -u cloudflared -n 50
```

---

## Troubleshooting

### App not accessible from internet

**Cloudflare:**
```bash
sudo systemctl status cloudflared
sudo systemctl restart cloudflared
```

**DuckDNS:**
```bash
# Check if port is open: https://www.yougetsignal.com/tools/open-ports/
# Test ports 80 and 443
```

### "Invalid authentication token"

```bash
# Verify token in .env
cat /opt/cookedtogether/app/recipe_app/.env | grep RECIPE_AUTH_TOKEN

# Restart app
sudo systemctl restart cookedtogether
```

### Database errors

```bash
# Restore from backup
cd /opt/cookedtogether/app/recipe_app
cp ~/backups/database_20240115.db database.db
sudo systemctl restart cookedtogether
```

### Pi running slow

```bash
# Check resources
free -h
df -h

# Reduce workers
nano gunicorn_config.py
# Change: workers = 2

sudo systemctl restart cookedtogether
```

---

## Update Recipe App

When you push changes to GitHub:

```bash
cd /opt/cookedtogether/app
git pull

cd recipe_app
source venv/bin/activate
pip install -r requirements.txt  # If dependencies changed

sudo systemctl restart cookedtogether
```

---

## Cost Summary

**One-time:**
- Raspberry Pi 4 (4GB): ~$55
- SD Card (32GB): ~$10
- Domain name: ~$12/year
- **Total: ~$77**

**Ongoing:**
- Domain renewal: ~$12/year
- Electricity (Pi 24/7): ~$5/year
- **Total: ~$17/year (~$1.40/month)**

**Way cheaper than any cloud hosting!** 🎉

---

## Quick Commands Reference

```bash
# Restart everything
sudo systemctl restart cookedtogether nginx cloudflared

# View logs
sudo journalctl -u cookedtogether -f

# Check status
sudo systemctl status cookedtogether
sudo systemctl status nginx
sudo systemctl status cloudflared

# Update app
cd /opt/cookedtogether/app && git pull
sudo systemctl restart cookedtogether

# Backup database manually
cp database.db database_backup_$(date +%Y%m%d).db

# Find Pi's IP
hostname -I
tailscale ip -4  # If using Tailscale
```

---

## Success! 🎉

Your recipe app is now:
- ✅ Running on your Raspberry Pi
- ✅ Accessible from anywhere in the world
- ✅ Secured with HTTPS
- ✅ Protected with authentication token
- ✅ Ready for your family to use!

**Your mother can now add her recipes from her house!**

---

## Full Documentation

- **Detailed Pi Setup:** [DEPLOYMENT_RASPBERRY_PI.md](DEPLOYMENT_RASPBERRY_PI.md)
- **Network Explanation:** [NETWORK_SETUP_EXPLAINED.md](NETWORK_SETUP_EXPLAINED.md)
- **Token Management:** [deployment/SECRETS_MANAGEMENT.md](deployment/SECRETS_MANAGEMENT.md)
- **General Deployment:** [DEPLOYMENT.md](DEPLOYMENT.md)

**Questions?** Check the logs first, then consult the full guides!
