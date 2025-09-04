#!/bin/bash

# Deployment script for QR Check-in System to Linode (Docker Compose)
# Usage: ./deploy_to_linode.sh <linode-ip> <username>

if [ $# -lt 2 ]; then
    echo "Usage: $0 <linode-ip> <username>"
    echo "Example: $0 192.168.1.100 root"
    exit 1
fi

LINODE_IP=$1
USERNAME=$2
REMOTE_DIR="/opt/qr-checkin-system"

echo "🚀 Deploying QR Check-in System to Linode server (Docker Compose)..."
echo "Server: $USERNAME@$LINODE_IP"
echo "Remote directory: $REMOTE_DIR"
echo ""

# Create remote directory if it doesn't exist
echo "📁 Creating remote directory..."
ssh $USERNAME@$LINODE_IP "mkdir -p $REMOTE_DIR"

# Sync files using rsync (excluding unnecessary files)
echo "📤 Transferring files..."
rsync -avz --progress \
    --exclude='.git' \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='node_modules' \
    --exclude='.env' \
    --exclude='*.sqlite3' \
    --exclude='media/*' \
    --exclude='staticfiles/*' \
    --exclude='venv' \
    --exclude='.venv' \
    --exclude='bfg-1.14.0.jar' \
    --exclude='.vscode' \
    --exclude='*.log' \
    --exclude='.DS_Store' \
    ./ $USERNAME@$LINODE_IP:$REMOTE_DIR/

echo ""
echo "✅ Files transferred successfully!"
echo ""
echo "📋 Next steps on the server:"
echo "----------------------------------------"
echo "1. SSH into server:"
echo "   ssh $USERNAME@$LINODE_IP"
echo ""
echo "2. Navigate to project:"
echo "   cd $REMOTE_DIR"
echo ""
echo "3. Create environment files:"
echo "   # Backend .env"
echo "   cat > backend/.env << 'EOF'"
echo "SECRET_KEY=your-secret-key-here"
echo "DEBUG=False"
echo "ALLOWED_HOSTS=your-domain.com,your-linode-ip"
echo "DATABASE_URL=postgresql://postgres:password@db:5432/qrcheckin"
echo "EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend"
echo "EMAIL_HOST=smtp.gmail.com"
echo "EMAIL_PORT=587"
echo "EMAIL_USE_TLS=True"
echo "EMAIL_HOST_USER=your-email@gmail.com"
echo "EMAIL_HOST_PASSWORD=your-app-password"
echo "DEFAULT_FROM_EMAIL=your-email@gmail.com"
echo "EOF"
echo ""
echo "   # Frontend .env"
echo "   cat > frontend/.env << 'EOF'"
echo "VITE_API_URL=http://your-domain.com/api"
echo "EOF"
echo ""
echo "4. Build and start containers:"
echo "   docker-compose up -d --build"
echo ""
echo "5. Run migrations:"
echo "   docker-compose exec backend python manage.py migrate"
echo ""
echo "6. Create superuser:"
echo "   docker-compose exec backend python manage.py createsuperuser"
echo ""
echo "7. Collect static files:"
echo "   docker-compose exec backend python manage.py collectstatic --noinput"
echo ""
echo "----------------------------------------"
echo "🔒 For production with external database:"
echo "   - Update DATABASE_URL in backend/.env"
echo "   - Remove 'db' service from docker-compose.yml"
echo "   - Use managed database service URL"