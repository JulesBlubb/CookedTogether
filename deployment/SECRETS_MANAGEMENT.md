# Secrets Management Guide

## How to Handle the Authentication Token Securely

### Overview

Your recipe app uses a `RECIPE_AUTH_TOKEN` to protect the `/add_recipe` and `/edit_recipe` endpoints. This token must be kept secret but accessible to authorized family members.

---

## ⚠️ CRITICAL: What NOT to Do

**NEVER:**
- ❌ Commit the `.env` file to Git/GitHub
- ❌ Share tokens via email or SMS
- ❌ Post tokens in Slack, Discord, or public forums
- ❌ Hardcode tokens in source code
- ❌ Use the default example token in production

---

## ✅ Recommended Methods

### Method 1: Environment Variables (For Server/Production)

**Best for:** VPS, cloud deployments, Docker

```bash
# On your production server
export RECIPE_AUTH_TOKEN="your-secure-token-here"

# Make it permanent (add to ~/.bashrc or ~/.profile)
echo 'export RECIPE_AUTH_TOKEN="your-secure-token-here"' >> ~/.bashrc
source ~/.bashrc
```

**For systemd services:**
The token is automatically loaded from `/home/cookedtogether/app/recipe_app/.env` via the systemd service file.

### Method 2: Password Manager (For Sharing with Family)

**Recommended tools:**
- **1Password** - Family plan with shared vaults
- **Bitworm** - Free for families
- **LastPass** - Family plan
- **KeePassXC** - Open source, file-based

**How to share:**
1. Store the token in a "Secure Note" or "Password" entry
2. Create a shared vault for family members
3. Share only the specific token entry
4. Family members access via their password manager app

**Example 1Password setup:**
```
Title: Cooked Together - Recipe Auth Token
Username: (leave empty)
Password: ey-Wd56civFqa5hVMb0vq9-0Y2Hi0GFDmP9OYrUfEoB
Website: https://your-recipe-site.com/add_recipe
Notes: Use this token to create/edit recipes
```

### Method 3: Git Secrets (For CI/CD)

**GitHub Actions:**
1. Go to: Repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `RECIPE_AUTH_TOKEN`
4. Value: `your-secure-token`

**GitLab CI/CD:**
1. Go to: Settings → CI/CD → Variables
2. Add variable `RECIPE_AUTH_TOKEN`
3. Mark as "Protected" and "Masked"

**Access in workflows:**
```yaml
# .github/workflows/deploy.yml
env:
  RECIPE_AUTH_TOKEN: ${{ secrets.RECIPE_AUTH_TOKEN }}
```

### Method 4: Docker Secrets (For Docker Deployments)

**Docker Compose:**
```yaml
# docker-compose.yml
services:
  app:
    image: cookedtogether:latest
    environment:
      - RECIPE_AUTH_TOKEN=${RECIPE_AUTH_TOKEN}
    env_file:
      - .env.prod  # Never commit this file!
```

**Docker Swarm:**
```bash
# Create secret
echo "your-token" | docker secret create recipe_auth_token -

# Use in service
docker service create \
  --secret recipe_auth_token \
  --name cookedtogether \
  cookedtogether:latest
```

---

## How Family Members Use the Token

### For Web Interface (Recommended)

1. **Visit the add recipe page:**
   ```
   https://your-recipe-site.com/add_recipe
   ```

2. **Enter the token when prompted:**
   - A token input field appears at the top of the form
   - Paste the token from your password manager
   - Token is stored in browser session (secure)

3. **Create/edit recipes:**
   - Once authenticated, you can create and edit recipes
   - Token persists for the browser session

### For API/Scripts (Advanced)

```bash
# Using curl
curl -X POST https://your-recipe-site.com/add_recipe \
  -H "Content-Type: application/json" \
  -H "X-Auth-Token: your-token-here" \
  -d '{"title": "Test Recipe", ...}'
```

---

## Token Rotation (If Compromised)

If the token is accidentally exposed:

### 1. Generate a New Token

```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
```

### 2. Update on Server

```bash
# SSH to server
ssh user@your-server

# Update .env file
nano /home/cookedtogether/app/recipe_app/.env
# Change RECIPE_AUTH_TOKEN to new value

# Restart application
sudo systemctl restart cookedtogether
```

### 3. Notify Family Members

Send a secure message:
```
The recipe app token has been updated for security.
Please update your stored token to:
[share new token via password manager]
```

---

## Security Best Practices

### ✅ DO:
- Use a password manager to store and share tokens
- Generate strong, random tokens (32+ characters)
- Rotate tokens annually or after suspected compromise
- Use HTTPS in production (encrypts token in transit)
- Limit token sharing to trusted family members only
- Keep the `.env` file permissions restricted: `chmod 600 .env`

### ❌ DON'T:
- Share tokens in plain text messages
- Write tokens on paper/sticky notes
- Use simple or guessable tokens
- Reuse tokens from other services
- Share screenshots containing tokens
- Store tokens in browser bookmarks

---

## Checking Current Token Status

### On the Server:

```bash
# View current token (requires sudo/owner access)
grep RECIPE_AUTH_TOKEN /home/cookedtogether/app/recipe_app/.env

# Verify environment variable is set
echo $RECIPE_AUTH_TOKEN
```

### Test Token Validity:

```bash
# Should return 403 Forbidden (without token)
curl https://your-recipe-site.com/add_recipe

# Should return 200 OK (with correct token)
curl https://your-recipe-site.com/add_recipe \
  -H "X-Auth-Token: your-token-here"
```

---

## Troubleshooting

### "Invalid or missing authentication token"

**Causes:**
- Token not set in `.env` file
- Environment variable not loaded
- Typo in token value
- Token contains extra spaces/newlines

**Solutions:**
```bash
# Check .env file exists and has correct format
cat .env
# Should show: RECIPE_AUTH_TOKEN=your-token-here (no quotes, no spaces)

# Restart application to reload env vars
sudo systemctl restart cookedtogether

# Verify token in running process
sudo systemctl show cookedtogether --property=Environment
```

### Token works locally but not in production

**Cause:** `.env` file not deployed or has wrong permissions

**Solution:**
```bash
# Ensure .env exists on server
ls -la /home/cookedtogether/app/recipe_app/.env

# Check permissions (should be readable by app user)
sudo chmod 640 /home/cookedtogether/app/recipe_app/.env
sudo chown cookedtogether:www-data /home/cookedtogether/app/recipe_app/.env
```

---

## Example: Complete Setup Flow

```bash
# 1. Generate secure tokens
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
RECIPE_AUTH_TOKEN=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')

# 2. Create .env file
cat > .env <<EOF
SECRET_KEY=$SECRET_KEY
RECIPE_AUTH_TOKEN=$RECIPE_AUTH_TOKEN
FLASK_ENV=production
FLASK_DEBUG=0
EOF

# 3. Secure the file
chmod 600 .env

# 4. Save token to password manager
echo "Save this to 1Password/Bitwarden:"
echo "RECIPE_AUTH_TOKEN=$RECIPE_AUTH_TOKEN"

# 5. Deploy and start application
# (follow DEPLOYMENT.md)
```

---

## Questions?

- **Where is the token used?** In `/add_recipe` and `/edit_recipe` routes
- **Can I have multiple tokens?** No, only one token is active at a time
- **Is the token encrypted?** No, but it's securely random and hard to guess
- **What if I forget the token?** Access the server and check the `.env` file
- **Can I disable token auth?** Not recommended, but you can modify `app.py`

**For more help:** Check logs with `sudo journalctl -u cookedtogether`
