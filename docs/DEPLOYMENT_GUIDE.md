# Production Deployment Guide: Enterprise AI Grocery Inventory Platform

This document details the step-by-step instructions for deploying the **Enterprise AI Grocery Inventory Management Platform** into production using Docker Compose, Nginx, PostgreSQL, Redis, FastAPI, and Next.js.

---

## 🏗️ Architecture Overview

The production environment operates as a multi-container Docker composition behind an Nginx reverse proxy gateway:

```
                  ┌────────────────────────┐
                  │    Internet / Client   │
                  └───────────┬────────────┘
                              │ HTTP :80 / HTTPS :443
                              ▼
                  ┌────────────────────────┐
                  │   Nginx Gateway        │
                  │   Reverse Proxy        │
                  └─────┬────────────┬─────┘
                        │            │
         ┌──────────────┘            └──────────────┐
         ▼                                          ▼
┌──────────────────┐                       ┌──────────────────┐
│ Next.js Frontend │                       │  FastAPI Backend │
│ Container (:3000)│                       │ Container (:8000)│
└──────────────────┘                       └────────┬─────────┘
                                                    │
                                     ┌──────────────┴──────────────┐
                                     ▼                             ▼
                            ┌────────────────┐            ┌────────────────┐
                            │   PostgreSQL   │            │   Redis Cache  │
                            │  DB (:5432)    │            │   Container    │
                            └────────────────┘            └────────────────┘
```

---

## 📋 Prerequisites

1. **Host Environment**: Linux Server (Ubuntu 22.04 LTS recommended) or Windows Server with Docker Desktop.
2. **Software**:
   - Docker Engine v24.0+
   - Docker Compose v2.20+
   - NVIDIA GPU Drivers + NVIDIA Container Toolkit *(Optional for GPU acceleration)*

---

## ⚙️ Step 1: Clone Repository & Configure Environment

```bash
# 1. Copy production environment variables template
cp .env.production .env

# 2. Modify secrets in .env
nano .env
```

Ensure the following variables are configured securely in `.env`:
* `POSTGRES_PASSWORD`: Strong password for PostgreSQL.
* `JWT_SECRET`: Random 64-character secret key.
* `NEXT_PUBLIC_API_URL`: Domain URL pointing to the Nginx proxy (e.g., `http://inventory.yourdomain.com`).

---

## 🚀 Step 2: Build & Launch Multi-Container Stack

```bash
# Build and start all services in detached mode
docker-compose --env-file .env up -d --build
```

---

## 🔍 Step 3: Verify Service Health & Connectivity

```bash
# Check running container statuses
docker-compose ps
```

Expected Output:
```
NAME               STATUS                  PORTS
grocery-db         Up (healthy)            0.0.0.0:5432->5432/tcp
grocery-redis      Up (healthy)            0.0.0.0:6379->6379/tcp
grocery-backend    Up (healthy)            0.0.0.0:8000->8000/tcp
grocery-frontend   Up                      0.0.0.0:3000->3000/tcp
grocery-nginx      Up                      0.0.0.0:80->80/tcp
```

### Health Check Endpoints
* Nginx Gateway: `http://localhost/nginx-health`
* Backend API Health: `http://localhost/api/v1/health`
* Swagger Documentation: `http://localhost/docs`
* Frontend App: `http://localhost`

---

## 🔒 Step 4: SSL Certificate Setup (Let's Encrypt Certbot)

To enable HTTPS on your production server:

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL Certificate
sudo certbot --nginx -d inventory.yourdomain.com
```

---

## 📊 Step 5: Monitoring & Maintenance

```bash
# View real-time container logs
docker-compose logs -f --tail=100 backend

# View Nginx access logs
docker-compose exec nginx tail -f /var/log/nginx/access_log.log

# Database Backup Command
docker-compose exec db pg_dump -U postgres grocery_db > grocery_backup_$(date +%Y%m%m).sql
```
