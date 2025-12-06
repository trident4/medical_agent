# Docker Deployment Guide

This project has two Docker Compose configurations:

## 🔧 Development Setup (Current)

**File**: `docker-compose.yml`

**Usage**:
```bash
docker-compose up
```

**Characteristics**:
- FastAPI exposed directly on port **8000**
- Fast startup, no Nginx overhead
- Good for local development and testing
- Access API at: `http://localhost:8000`

**Services**:
- `web` - FastAPI application (port 8000)
- `db` - MySQL database (port 3307)
- `phpmyadmin` - Database admin (port 8080)

---

## 🚀 Production Setup (New - With Nginx)

**File**: `docker-compose.prod.yml`

**Usage**:
```bash
docker-compose -f docker-compose.prod.yml up
```

**Characteristics**:
- Nginx reverse proxy on port **80**
- FastAPI not directly exposed (internal only)
- Production-ready with security headers
- Gzip compression enabled
- Better performance and security
- Access API at: `http://localhost` (port 80)

**Services**:
- `nginx` - Reverse proxy (port 80)
- `web` - FastAPI application (internal only)
- `db` - MySQL database (port 3307)
- `phpmyadmin` - Database admin (port 8080)

---

## 📊 Port Mapping Comparison

| Service | Development | Production (Nginx) |
|---------|-------------|-------------------|
| **API Access** | `localhost:8000` | `localhost:80` |
| **Database** | `localhost:3307` | `localhost:3307` |
| **phpMyAdmin** | `localhost:8080` | `localhost:8080` |
| **API Docs** | `localhost:8000/docs` | `localhost/docs` |

---

## 🎯 Quick Start

### First Time Setup

1. **Copy environment file**:
   ```bash
   cp .env.example .env_docker
   # Edit .env_docker with your settings
   ```

2. **Choose your setup**:

   **For Development**:
   ```bash
   docker-compose up -d
   ```

   **For Production**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Check if running**:
   ```bash
   docker-compose ps
   ```

4. **View logs**:
   ```bash
   # Development
   docker-compose logs -f web
   
   # Production
   docker-compose -f docker-compose.prod.yml logs -f nginx
   ```

---

## 🔄 Common Commands

### Development Mode

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# View logs
docker-compose logs -f

# Access database
docker-compose exec db mysql -u root -p
```

### Production Mode

```bash
# Start services
docker-compose -f docker-compose.prod.yml up -d

# Stop services
docker-compose -f docker-compose.prod.yml down

# Rebuild after code changes
docker-compose -f docker-compose.prod.yml up -d --build

# View Nginx logs
docker-compose -f docker-compose.prod.yml logs -f nginx

# View app logs
docker-compose -f docker-compose.prod.yml logs -f web
```

---

## 🧪 Testing Your Setup

### Development Setup

```bash
# Start
docker-compose up -d

# Test API
curl http://localhost:8000/health

# Test docs
open http://localhost:8000/docs
```

### Production Setup

```bash
# Start
docker-compose -f docker-compose.prod.yml up -d

# Test API (through Nginx)
curl http://localhost/health

# Test docs (through Nginx)
open http://localhost/docs

# Check Nginx is running
docker-compose -f docker-compose.prod.yml exec nginx nginx -t
```

---

## 🛠️ Troubleshooting

### Port Already in Use

**Error**: `Bind for 0.0.0.0:80 failed: port is already allocated`

**Solution**:
```bash
# Find what's using port 80
sudo lsof -i :80

# Stop the service or change port in docker-compose.prod.yml
```

### Nginx Can't Connect to Backend

**Error**: `502 Bad Gateway`

**Solution**:
```bash
# Check if web service is running
docker-compose -f docker-compose.prod.yml ps

# Check web service logs
docker-compose -f docker-compose.prod.yml logs web

# Restart services
docker-compose -f docker-compose.prod.yml restart
```

### Database Connection Issues

**Solution**:
```bash
# Check database is healthy
docker-compose -f docker-compose.prod.yml ps db

# Check database logs
docker-compose -f docker-compose.prod.yml logs db

# Restart database
docker-compose -f docker-compose.prod.yml restart db
```

---

## 🌐 Deploying to Production Server

When deploying to a real server (VPS, cloud, etc.):

1. **Use production setup**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

2. **Configure domain** (optional):
   - Update `nginx.conf` with your domain name
   - Set up SSL/HTTPS (use Let's Encrypt)

3. **Security checklist**:
   - [ ] Change default passwords in `.env_docker`
   - [ ] Use strong SECRET_KEY
   - [ ] Enable HTTPS
   - [ ] Remove phpMyAdmin in production (or restrict access)
   - [ ] Set up firewall rules
   - [ ] Regular backups of database

---

## 📝 What's Different?

### nginx.conf Features

- **Security Headers**: Protects against XSS, clickjacking
- **Gzip Compression**: Reduces bandwidth usage
- **Timeouts**: Configured for AI processing (60s)
- **Health Check**: Separate endpoint with no logging
- **WebSocket Support**: Ready for real-time features

### docker-compose.prod.yml Features

- **Nginx Service**: Alpine-based, lightweight
- **Network Isolation**: Services communicate via dedicated network
- **No Direct Exposure**: FastAPI only accessible through Nginx
- **Production Restart Policy**: Auto-restart on failures

---

## 🎓 Learning Resources

- **Nginx Docs**: https://nginx.org/en/docs/
- **Docker Compose**: https://docs.docker.com/compose/
- **FastAPI Deployment**: https://fastapi.tiangolo.com/deployment/

---

## ✅ Next Steps

1. Test production setup locally
2. Deploy to a platform (Render, Railway, Fly.io)
3. Set up CI/CD for automatic deployments
4. Add monitoring and logging
5. Configure SSL/HTTPS for production domain
