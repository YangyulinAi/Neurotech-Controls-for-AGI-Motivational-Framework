#!/bin/bash

# Neurotech Controls for AGI Motivational Framework - Management Script
# This script provides menu-driven deployment and management

set -e

show_menu() {
    echo ""
    echo "🧠 Neurotech Controls for AGI Motivational Framework"
    echo "===================================================="
    echo ""
    echo "Please select an option:"
    echo "1) Deploy (First-time setup and configuration)"
    echo "2) Start (Launch the application)"
    echo "3) Stop (Stop the running application)"
    echo "4) Uninstall (Remove all components)"
    echo "5) Exit"
    echo ""
    read -p "Enter your choice (1-5): " choice
    echo ""
}

configure_firewall() {
    echo ""
    echo "🔥 Firewall Configuration"
    echo "========================"
    echo "Do you want to configure firewall rules?"
    echo "This will open necessary ports for the application."
    echo ""
    read -p "Configure firewall? (y/N): " configure_fw
    
    if [[ $configure_fw =~ ^[Yy]$ ]]; then
        echo "🔧 Configuring firewall..."
        
        # Install ufw if not present
        if ! command -v ufw &> /dev/null; then
            echo "Installing UFW firewall..."
            sudo apt-get update
            sudo apt-get install -y ufw
        fi
        
        # Enable firewall with default rules
        echo "Setting up firewall rules..."
        sudo ufw --force reset
        sudo ufw default deny incoming
        sudo ufw default allow outgoing
        
        # Allow SSH (important to keep access)
        sudo ufw allow ssh
        echo "✅ SSH access allowed (port 22)"
        
        # Allow application port (read from .env if exists)
        if [ -f ".env" ]; then
            APP_PORT=$(grep "^PORT=" .env | cut -d'=' -f2)
        else
            APP_PORT=5000
        fi
        sudo ufw allow $APP_PORT
        echo "✅ Application port allowed ($APP_PORT)"
        
        # Check if nginx is installed and configured
        if [ -f "/etc/nginx/sites-enabled/neurotech-agi" ] || [ -f "nginx-config/neurotech-agi.conf" ]; then
            # Allow HTTP and HTTPS for reverse proxy
            sudo ufw allow 80
            sudo ufw allow 443
            echo "✅ HTTP/HTTPS ports allowed (80, 443) for reverse proxy"
        else
            echo "ℹ️  No reverse proxy configuration found, skipping HTTP/HTTPS ports"
        fi
        
        # Enable firewall
        sudo ufw --force enable
        
        echo ""
        echo "🎉 Firewall configured successfully!"
        echo "📋 Current firewall status:"
        sudo ufw status
        echo ""
        echo "⚠️  Important: If you lose SSH access, you can disable the firewall from the server console:"
        echo "   sudo ufw disable"
    else
        echo "⏭️  Skipping firewall configuration"
        echo "💡 Manual firewall setup may be needed for production environments"
    fi
}

deploy_system() {
    echo "📦 Starting deployment process..."
    echo "=================================="
    
    # Ask for port configuration
    echo "🌐 Port Configuration"
    echo "===================="
    echo "Choose the port for the application:"
    read -p "Enter port number (default: 5000): " user_port
    
    # Validate and set port
    if [[ -z "$user_port" ]]; then
        APP_PORT=5000
        echo "Using default port: 5000"
    elif [[ "$user_port" =~ ^[0-9]+$ ]] && [ "$user_port" -ge 1024 ] && [ "$user_port" -le 65535 ]; then
        APP_PORT=$user_port
        echo "Using port: $APP_PORT"
    else
        echo "❌ Invalid port. Using default port 5000."
        APP_PORT=5000
    fi
    
    # Store port configuration
    echo "PORT=$APP_PORT" > .env
    echo "HOST=0.0.0.0" >> .env
    echo "NODE_ENV=development" >> .env
    echo ""

    # Check if this is first run (no node_modules)
    if [ ! -d "node_modules" ]; then
        echo "🔧 First run detected - performing setup..."
        
        # Check available disk space
        AVAILABLE_SPACE=$(df / | tail -1 | awk '{print $4}')
        echo "📊 Available disk space: $(($AVAILABLE_SPACE / 1024))MB"
        
        if [ $AVAILABLE_SPACE -lt 1500000 ]; then
            echo "⚠️  Warning: Low disk space detected (< 1.5GB). Cleaning up..."
            sudo apt-get autoremove -y || true
            sudo apt-get autoclean || true
            pip3 cache purge || true
        fi
        
        # Check prerequisites
        if ! command -v node &> /dev/null; then
            echo "❌ Node.js is not installed. Please install Node.js 18+ first."
            exit 1
        fi
        
        if ! command -v python3 &> /dev/null; then
            echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
            exit 1
        fi
        
        echo "✅ Prerequisites check passed"
        
        # Install Node.js dependencies
        echo "📦 Installing Node.js dependencies..."
        npm install
        
        # Install Python dependencies
        echo "🐍 Installing Python dependencies..."
        
        # Check if requirements_phi.txt exists
        if [ -f "requirements_phi.txt" ]; then
            echo "   Using requirements_phi.txt..."
            # Create virtual environment to avoid externally-managed-environment error
            python3 -m venv venv --system-site-packages || true
            source venv/bin/activate || true
            pip install --upgrade pip
            pip install -r requirements_phi.txt --no-cache-dir
        else
            echo "   Installing dependencies individually..."
            # Use --break-system-packages flag to override externally-managed-environment
            pip3 install --break-system-packages --no-cache-dir numpy==1.21.6 scipy==1.7.3 pandas==1.3.5
            pip3 install --break-system-packages --no-cache-dir fastapi==0.85.0 uvicorn==0.18.3 websockets==10.4
            pip3 install --break-system-packages --no-cache-dir onnxruntime==1.12.1 pyyaml==6.0 paho-mqtt==1.6.1
            pip3 install --break-system-packages --no-cache-dir requests==2.28.2
        fi
        
        # Create necessary directories
        echo "📁 Creating project directories..."
        mkdir -p data/training\ set
        mkdir -p model
        mkdir -p model_training
        
        # Set permissions for Python scripts (if they exist)
        [ -f "analyze_set_file.py" ] && chmod +x analyze_set_file.py || true
        
        # Verify installation
        echo "🔍 Verifying PyTorch installation..."
        python3 -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')" 2>/dev/null || echo "PyTorch verification skipped"
        
        echo "🎉 Setup completed successfully!"
        echo ""
        
        # Ask about reverse proxy configuration
        echo "🌐 Reverse Proxy Configuration"
        echo "============================================="
        echo "Do you want to generate nginx configuration files?"
        echo "Note: This will create configuration files for manual nginx setup on your server."
        echo ""
        read -p "Generate nginx configuration? (y/N): " configure_proxy
        
        if [[ $configure_proxy =~ ^[Yy]$ ]]; then
            echo ""
            echo "📝 Please provide the following information:"
            
            # Get domain URL
            read -p "Enter your domain URL (e.g., yourdomain.com): " domain_url
            if [[ -z "$domain_url" ]]; then
                echo "❌ Domain URL is required for reverse proxy configuration"
                return 1
            fi
            
            # SSL Certificate Configuration
            echo ""
            echo "SSL Certificate Configuration:"
            echo "1) Use existing SSL certificate files"
            echo "2) Generate self-signed certificate (for testing)"
            echo "3) Skip SSL (HTTP only - not recommended for production)"
            echo ""
            read -p "Choose option (1/2/3): " ssl_option
            
            case $ssl_option in
                1)
                    echo ""
                    echo "Please provide paths to your SSL certificate files:"
                    read -p "Enter SSL certificate path (e.g., /etc/ssl/certs/your-cert.pem): " ssl_cert_path
                    read -p "Enter SSL private key path (e.g., /etc/ssl/private/your-key.key): " ssl_key_path
                    
                    # Validate SSL certificate paths exist
                    if [[ ! -f "$ssl_cert_path" ]]; then
                        echo "❌ SSL certificate file not found: $ssl_cert_path"
                        echo "Please ensure the certificate file exists before configuring nginx"
                        return 1
                    fi
                    
                    if [[ ! -f "$ssl_key_path" ]]; then
                        echo "❌ SSL private key file not found: $ssl_key_path"
                        echo "Please ensure the private key file exists before configuring nginx"  
                        return 1
                    fi
                    use_ssl=true
                    ;;
                2)
                    echo ""
                    echo "🔧 Generating self-signed SSL certificate..."
                    
                    # Create SSL directory in project
                    mkdir -p ssl-certs
                    
                    # Generate self-signed certificate
                    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                        -keyout ssl-certs/selfsigned.key \
                        -out ssl-certs/selfsigned.crt \
                        -subj "/C=US/ST=State/L=City/O=Organization/CN=$domain_url" 2>/dev/null
                    
                    if [[ $? -eq 0 ]]; then
                        ssl_cert_path="$(pwd)/ssl-certs/selfsigned.crt"
                        ssl_key_path="$(pwd)/ssl-certs/selfsigned.key"
                        echo "✅ Self-signed certificate generated successfully"
                        echo "📄 Certificate: $ssl_cert_path"
                        echo "🔑 Private key: $ssl_key_path"
                        echo ""
                        echo "⚠️  Warning: Self-signed certificates will show security warnings in browsers"
                        echo "   Use only for testing. Get a proper certificate for production."
                        use_ssl=true
                    else
                        echo "❌ Failed to generate self-signed certificate"
                        echo "Falling back to HTTP-only configuration"
                        use_ssl=false
                    fi
                    ;;
                3)
                    echo ""
                    echo "⚠️  Configuring HTTP-only (no SSL)"
                    echo "   This is not recommended for production environments"
                    use_ssl=false
                    ;;
                *)
                    echo "❌ Invalid option. Defaulting to HTTP-only configuration"
                    use_ssl=false
                    ;;
            esac
            
            # Create nginx configuration
            echo ""
            echo "🔧 Creating nginx configuration..."
            
            # Create nginx configuration directory in project
            mkdir -p nginx-config
            
            # Generate nginx config file using template files
            if [[ "$use_ssl" == "true" ]]; then
                # Use HTTPS template
                cp nginx-template.conf nginx-config/neurotech-agi.conf
                # Replace placeholders
                sed -i "s/DOMAIN_PLACEHOLDER/$domain_url/g" nginx-config/neurotech-agi.conf
                sed -i "s|SSL_CERT_PLACEHOLDER|$ssl_cert_path|g" nginx-config/neurotech-agi.conf
                sed -i "s|SSL_KEY_PLACEHOLDER|$ssl_key_path|g" nginx-config/neurotech-agi.conf
                sed -i "s/PORT_PLACEHOLDER/$APP_PORT/g" nginx-config/neurotech-agi.conf
            else
                # Use HTTP-only template
                cp nginx-template-http.conf nginx-config/neurotech-agi.conf
                # Replace placeholders
                sed -i "s/DOMAIN_PLACEHOLDER/$domain_url/g" nginx-config/neurotech-agi.conf
                sed -i "s/PORT_PLACEHOLDER/$APP_PORT/g" nginx-config/neurotech-agi.conf
            fi
            
            # Create installation instructions with SSL-specific info
            if [[ "$use_ssl" == "true" ]]; then
                cat > nginx-config/INSTALL.md <<INSTALL_EOF
# Nginx Configuration Installation (HTTPS)

## Prerequisites
\`\`\`bash
# Install nginx (Ubuntu/Debian)
sudo apt update
sudo apt install nginx

# Or install nginx (CentOS/RHEL)
sudo yum install nginx
# or
sudo dnf install nginx
\`\`\`

## SSL Certificate Files
This configuration requires SSL certificate files:
- **Certificate**: $ssl_cert_path
- **Private Key**: $ssl_key_path

### If using self-signed certificates:
⚠️  **Warning**: Self-signed certificates will show security warnings in browsers.
For production, obtain proper SSL certificates from:
- Let's Encrypt (free): https://letsencrypt.org/
- Commercial CA: Cloudflare, DigiCert, etc.

## Installation Steps

1. **Copy SSL certificates (if not already in place):**
\`\`\`bash
# If using self-signed certificates generated by this script:
sudo mkdir -p /etc/ssl/certs /etc/ssl/private
sudo cp $ssl_cert_path /etc/ssl/certs/
sudo cp $ssl_key_path /etc/ssl/private/
sudo chmod 644 /etc/ssl/certs/selfsigned.crt
sudo chmod 600 /etc/ssl/private/selfsigned.key
\`\`\`

2. **Copy configuration file:**
\`\`\`bash
sudo cp neurotech-agi.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/neurotech-agi /etc/nginx/sites-enabled/
\`\`\`

3. **Remove default site (optional):**
\`\`\`bash
sudo rm /etc/nginx/sites-enabled/default
\`\`\`

4. **Test configuration:**
\`\`\`bash
sudo nginx -t
\`\`\`

5. **Restart nginx:**
\`\`\`bash
sudo systemctl restart nginx
sudo systemctl enable nginx
\`\`\`

6. **Configure firewall:**
\`\`\`bash
sudo ufw allow 'Nginx Full'
# or
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
\`\`\`

## Access
- **HTTPS**: https://$domain_url
- **HTTP**: Automatically redirects to HTTPS

## Troubleshooting

If nginx fails to start:
1. Check certificate file paths exist and are readable
2. Verify domain name is correct
3. Test configuration with: \`sudo nginx -t\`
4. Check nginx error logs: \`sudo tail -f /var/log/nginx/error.log\`
INSTALL_EOF
            else
                cat > nginx-config/INSTALL.md <<INSTALL_EOF
# Nginx Configuration Installation (HTTP Only)

## Prerequisites
\`\`\`bash
# Install nginx (Ubuntu/Debian)
sudo apt update
sudo apt install nginx

# Or install nginx (CentOS/RHEL)  
sudo yum install nginx
# or
sudo dnf install nginx
\`\`\`

## Installation Steps

1. **Copy configuration file:**
\`\`\`bash
sudo cp neurotech-agi.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/neurotech-agi /etc/nginx/sites-enabled/
\`\`\`

2. **Remove default site (optional):**
\`\`\`bash
sudo rm /etc/nginx/sites-enabled/default
\`\`\`

3. **Test configuration:**
\`\`\`bash
sudo nginx -t
\`\`\`

4. **Restart nginx:**
\`\`\`bash
sudo systemctl restart nginx
sudo systemctl enable nginx
\`\`\`

5. **Configure firewall:**
\`\`\`bash
sudo ufw allow 'Nginx HTTP'
# or
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --reload
\`\`\`

## Access
- **HTTP**: http://$domain_url

⚠️  **Security Notice**: This configuration uses HTTP only (no encryption).
For production environments, consider using HTTPS with proper SSL certificates.

## Troubleshooting

If nginx fails to start:
1. Verify domain name is correct
2. Test configuration with: \`sudo nginx -t\`
3. Check nginx error logs: \`sudo tail -f /var/log/nginx/error.log\`
INSTALL_EOF
            fi
            
            echo ""
            echo "🎉 Nginx configuration files created successfully!"
            echo "📁 Location: ./nginx-config/"
            echo "📄 Config file: ./nginx-config/neurotech-agi.conf"
            echo "📖 Installation guide: ./nginx-config/INSTALL.md"
            echo ""
            
            # Ask if user wants to install nginx configuration automatically
            read -p "Do you want to install the nginx configuration automatically? (y/N): " install_nginx
            
            if [[ $install_nginx =~ ^[Yy]$ ]]; then
                echo "🔧 Installing nginx configuration..."
                
                # Check if nginx is installed
                if ! command -v nginx &> /dev/null; then
                    echo "📦 Installing nginx..."
                    if command -v apt &> /dev/null; then
                        sudo apt update && sudo apt install -y nginx
                    elif command -v yum &> /dev/null; then
                        sudo yum install -y nginx
                    elif command -v dnf &> /dev/null; then
                        sudo dnf install -y nginx
                    else
                        echo "❌ Cannot install nginx automatically. Please install it manually."
                        echo "Then run: sudo cp nginx-config/neurotech-agi.conf /etc/nginx/sites-available/"
                        return 1
                    fi
                fi
                
                # Create nginx directories
                sudo mkdir -p /etc/nginx/sites-available /etc/nginx/sites-enabled
                
                # Copy SSL certificates if they are self-signed
                if [[ "$ssl_option" == "2" && "$use_ssl" == "true" ]]; then
                    echo "📋 Installing self-signed certificates..."
                    sudo mkdir -p /etc/ssl/certs /etc/ssl/private
                    sudo cp ssl-certs/selfsigned.crt /etc/ssl/certs/
                    sudo cp ssl-certs/selfsigned.key /etc/ssl/private/
                    sudo chmod 644 /etc/ssl/certs/selfsigned.crt
                    sudo chmod 600 /etc/ssl/private/selfsigned.key
                    
                    # Update paths in config file for system installation
                    sed -i 's|ssl_certificate .*ssl-certs/selfsigned.crt;|ssl_certificate /etc/ssl/certs/selfsigned.crt;|g' nginx-config/neurotech-agi.conf
                    sed -i 's|ssl_certificate_key .*ssl-certs/selfsigned.key;|ssl_certificate_key /etc/ssl/private/selfsigned.key;|g' nginx-config/neurotech-agi.conf
                fi
                
                # Install configuration  
                sudo cp nginx-config/neurotech-agi.conf /etc/nginx/sites-available/neurotech-agi
                sudo ln -sf /etc/nginx/sites-available/neurotech-agi /etc/nginx/sites-enabled/neurotech-agi
                
                # Remove default nginx site
                sudo rm -f /etc/nginx/sites-enabled/default
                
                # Test nginx configuration
                echo "🧪 Testing nginx configuration..."
                if sudo nginx -t; then
                    echo "✅ Nginx configuration is valid"
                    
                    # Enable and restart nginx
                    sudo systemctl enable nginx
                    sudo systemctl restart nginx
                    
                    if sudo systemctl is-active --quiet nginx; then
                        echo "✅ Nginx started successfully"
                        
                        if [[ "$use_ssl" == "true" ]]; then
                            echo "📡 Your application is now available at: https://$domain_url"
                            echo "🔒 SSL certificate installed"
                        else
                            echo "📡 Your application is now available at: http://$domain_url"
                        fi
                        
                        echo "🔄 Note: Make sure your DNS points to this server"
                    else
                        echo "❌ Failed to start nginx. Check the logs:"
                        echo "sudo journalctl -u nginx --no-pager -l"
                    fi
                else
                    echo "❌ Nginx configuration test failed"
                    echo "Please check the configuration manually"
                fi
            else
                echo "📋 Manual Setup Required:"
                echo "1. Install nginx on your server"
                echo "2. Copy the configuration file to nginx sites-available"
                echo "3. Enable the site and restart nginx"
                echo "4. Follow the instructions in INSTALL.md"
                echo ""
                if [[ "$use_ssl" == "true" ]]; then
                    echo "📡 Your application will be available at: https://$domain_url"
                    echo "🔒 SSL certificate: $ssl_cert_path"
                    echo "🔑 SSL private key: $ssl_key_path"
                else
                    echo "📡 Your application will be available at: http://$domain_url"
                    echo "⚠️  Note: HTTP-only configuration (no encryption)"
                fi
            fi
        else
            echo "⏭️  Skipping reverse proxy configuration"
            echo "💡 You can run this script again later to configure reverse proxy"
        fi
        
        # Configure firewall
        configure_firewall
        
        echo ""
        echo "✅ Deployment completed successfully!"
        echo ""
        echo "🚀 Starting application automatically..."
        start_system_background
        echo "✅ Application started in background"
        echo ""
        echo "📋 Management commands:"
        echo "   • Use option 2 to view status and access URLs"
        echo "   • Use option 3 to stop the application"
    else
        echo "ℹ️  System already deployed. Use option 2 to start the application."
    fi
}

start_system_background() {
    # Get port from .env file
    if [ -f ".env" ]; then
        source .env
    else
        export PORT=5000
        export HOST=0.0.0.0
        export NODE_ENV=development
    fi
    
    # Kill any existing processes on the configured port
    pkill -f "node.*$PORT" 2>/dev/null || true
    pkill -f "npm run dev" 2>/dev/null || true
    sleep 2

    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi

    # Start the application in background
    nohup npm run dev > app.log 2>&1 &
    echo $! > app.pid
    
    # Wait a moment and check if it started successfully
    sleep 3
    if ps -p $(cat app.pid 2>/dev/null) > /dev/null 2>&1; then
        echo "✅ Application started successfully in background (PID: $(cat app.pid))"
    else
        echo "❌ Failed to start application. Check app.log for details."
        return 1
    fi
}

start_system() {
    echo "🚀 Application Status & Control"
    echo "==============================="
    
    # Check if system is deployed
    if [ ! -d "node_modules" ]; then
        echo "❌ System not deployed yet. Please run option 1 (Deploy) first."
        return 1
    fi
    
    # Get port from .env file
    if [ -f ".env" ]; then
        source .env
    else
        PORT=5000
    fi
    
    # Check if application is already running
    if [ -f "app.pid" ] && ps -p $(cat app.pid 2>/dev/null) > /dev/null 2>&1; then
        echo "✅ Application is already running (PID: $(cat app.pid))"
        echo ""
    else
        echo "❌ Application is not running. Starting now..."
        start_system_background
        echo ""
    fi
    
    # Check if model exists
    if [ ! -f "model/va_regressor.onnx" ]; then
        echo "⚠️  No trained model found at model/va_regressor.onnx"
        echo "   You can upload a model through the web interface or train a new one"
        echo ""
    fi

    # Display access URLs
    if [ -f "/etc/nginx/sites-enabled/neurotech-agi" ]; then
        domain_url=$(sudo grep "server_name" /etc/nginx/sites-enabled/neurotech-agi | head -1 | awk '{print $2}' | sed 's/;//' 2>/dev/null || echo "configured-domain")
        if sudo grep -q "listen 443 ssl" /etc/nginx/sites-enabled/neurotech-agi 2>/dev/null; then
            echo "🌐 Nginx reverse proxy: https://$domain_url"
        else
            echo "🌐 Nginx reverse proxy: http://$domain_url"
        fi
    elif [ -f "nginx-config/neurotech-agi.conf" ]; then
        domain_url=$(grep "server_name" nginx-config/neurotech-agi.conf | head -1 | awk '{print $2}' | sed 's/;//' 2>/dev/null || echo "configured-domain")
        echo "🌐 Nginx config ready: $domain_url (not yet installed)"
    fi
    
    # Get server IP for external access
    SERVER_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "your-server-ip")
    echo "🏠 Local URL: http://localhost:$PORT"
    echo "🌍 External URL: http://$SERVER_IP:$PORT"
    echo ""
    echo "📋 Application Control:"
    echo "   • Application runs in background independent of this script"
    echo "   • Use option 3 to stop the application"
    echo "   • Logs are available in: ./app.log"
    echo ""
    echo "🔧 Connection Troubleshooting:"
    echo "   • If external access fails, check your cloud provider's security groups"
    echo "   • Ensure port $PORT is open in your firewall settings"
    echo "   • For cloud instances (AWS/GCP/Azure), configure inbound rules for port $PORT"
}

stop_system() {
    echo "🛑 Stopping application..."
    echo "========================="
    
    # Get port from .env file
    if [ -f ".env" ]; then
        source .env
    else
        PORT=5000
    fi
    
    # Stop application using PID file
    if [ -f "app.pid" ]; then
        app_pid=$(cat app.pid)
        if ps -p $app_pid > /dev/null 2>&1; then
            echo "Stopping application (PID: $app_pid)..."
            kill $app_pid 2>/dev/null || true
            sleep 2
            
            # Force kill if still running
            if ps -p $app_pid > /dev/null 2>&1; then
                echo "Force stopping application..."
                kill -9 $app_pid 2>/dev/null || true
            fi
            
            rm -f app.pid
            echo "✅ Application stopped successfully"
        else
            echo "ℹ️  Application was not running (stale PID file removed)"
            rm -f app.pid
        fi
    else
        echo "ℹ️  No PID file found, attempting to stop any processes on port $PORT..."
        pkill -f "node.*$PORT" 2>/dev/null || true
        pkill -f "npm run dev" 2>/dev/null || true
        echo "✅ Cleanup completed"
    fi
}

uninstall_system() {
    echo "🗑️  Uninstalling system..."
    echo "=========================="
    echo "⚠️  This will remove all installed components and data!"
    echo "This action cannot be undone."
    echo ""
    read -p "Are you sure you want to uninstall? (type 'yes' to confirm): " confirm
    
    if [ "$confirm" = "yes" ]; then
        # Stop any running processes
        stop_system
        
        # Remove nginx configuration
        if [ -f "/etc/nginx/sites-enabled/neurotech-agi" ]; then
            echo "Removing nginx configuration..."
            sudo rm -f /etc/nginx/sites-enabled/neurotech-agi
            sudo rm -f /etc/nginx/sites-available/neurotech-agi
            
            # Remove SSL certificates if they were self-signed
            if [ -f "/etc/ssl/certs/selfsigned.crt" ]; then
                sudo rm -f /etc/ssl/certs/selfsigned.crt
                sudo rm -f /etc/ssl/private/selfsigned.key
                echo "✅ Self-signed certificates removed"
            fi
            
            sudo systemctl reload nginx 2>/dev/null || true
            echo "✅ Nginx configuration removed"
        fi
        
        # Remove Python virtual environment
        if [ -d "venv" ]; then
            echo "Removing Python virtual environment..."
            rm -rf venv
            echo "✅ Virtual environment removed"
        fi
        
        # Remove node modules
        if [ -d "node_modules" ]; then
            echo "Removing Node.js dependencies..."
            rm -rf node_modules
            echo "✅ Node modules removed"
        fi
        
        # Remove generated directories and files
        echo "Cleaning up generated files..."
        rm -rf dist/ .cache/ model_training/checkpoints/ nginx-config/ ssl-certs/ 2>/dev/null || true
        rm -f .env app.pid app.log nginx-template.conf nginx-template-http.conf 2>/dev/null || true
        
        echo ""
        echo "✅ Uninstallation completed successfully!"
        echo "To reinstall, run this script again and choose option 1."
    else
        echo "❌ Uninstallation cancelled"
    fi
}

# Main menu loop
while true; do
    show_menu
    case $choice in
        1)
            deploy_system
            read -p "Press Enter to return to menu..."
            ;;
        2)
            start_system
            read -p "Press Enter to return to menu..."
            ;;
        3)
            stop_system
            read -p "Press Enter to return to menu..."
            ;;
        4)
            uninstall_system
            read -p "Press Enter to return to menu..."
            ;;
        5)
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo "❌ Invalid option. Please choose 1-5."
            read -p "Press Enter to continue..."
            ;;
    esac
done