# Deployment Guide for VPS

This guide explains how to deploy your Rock Shield Construction website to a Virtual Private Server (VPS) running Linux (Ubuntu/Debian recommended).

## Prerequisites

On your VPS, you need to have the following installed:
- **Node.js** (Version 20 or higher)
- **npm** (usually comes with Node.js)
- **Git** (to clone the repository, or you can upload files manually)

## Deployment Steps

### 1. Upload Your Code
Transfer your project files to your VPS. You can use Git or SCP/SFTP.

```bash
# Example using git
git clone <your-repo-url>
cd <your-project-directory>
```

### 2. Install Dependencies
Install the required packages using npm.

```bash
npm install
```

### 3. Build the Application
This compiles the React frontend and the backend server into optimized production files.

```bash
npm run build
```
*This command will generate a `dist` folder containing the compiled application.*

### 4. Start the Application
You can start the production server with:

```bash
npm run start
```
The application will typically run on port **5000** (or whatever is defined in `PORT` env var).

## Running in the Background (Recommended)

For a production environment, you should use a process manager like **PM2** to keep your site running even if the server restarts or crashes.

### Install PM2
```bash
npm install -g pm2
```

### Start with PM2
```bash
pm2 start npm --name "rock-shield" -- run start
```

### Setup Startup Script
To ensure the app restarts on server reboot:
```bash
pm2 startup
pm2 save
```

## Using a Custom Domain (Nginx)

To point your domain (e.g., `rockshield.com`) to port 5000, use Nginx as a reverse proxy.

1. **Install Nginx:**
   ```bash
   sudo apt update
   sudo apt install nginx
   ```

2. **Configure Nginx:**
   Create a config file: `sudo nano /etc/nginx/sites-available/rockshield`

   ```nginx
   server {
       listen 80;
       server_name rockshield.com www.rockshield.com;

       location / {
           proxy_pass http://localhost:5000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
       }
   }
   ```

3. **Enable Site & Restart Nginx:**
   ```bash
   sudo ln -s /etc/nginx/sites-available/rockshield /etc/nginx/sites-enabled/
   sudo systemctl restart nginx
   ```

Your site should now be live!
