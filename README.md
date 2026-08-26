# Aetheria: AI-Powered Grocery Inventory Management System

A production-ready project foundation for automated shelf monitoring, grocery inventory tracking, and visual intelligence extraction. 

This repository implements a modular monorepo structure separating frontend visual experiences from computational backends, following strict **Clean Architecture** principles.

---

## Technical Stack Overview

* **Frontend**: Next.js 15 (App Router) + TypeScript + Tailwind CSS
* **Backend**: FastAPI (Python 3.11)
* **AI Engine**: Ultralytics YOLOv11 (Object Detection) + EasyOCR (Text/Expiry Extraction) + ByteTrack (Sequential Item Tracking)
* **Database & ORM**: PostgreSQL 15 + SQLAlchemy 2.0
* **Storage Interface**: Local, AWS S3, or Supabase Storage API options
* **Deployment & CI**: Docker + Docker Compose + GitHub Actions

---

## Architectural Layout (Clean Architecture)

The system enforces modular isolation of responsibilities, dividing code into layers based on dependency directions (outer layers point inward):

```
grocery-inventory-system/
│
├── backend/
│   ├── app/
│   │   ├── core/               # System configurations, security (JWT), database hooks
│   │   ├── domain/             # Enterprise logic (Entities & Interfaces)
│   │   │   ├── entities/       # Pure models (e.g. User, InventoryItem)
│   │   │   └── interfaces/     # Repository & Storage contracts
│   │   ├── data/               # Gateways & External adapters
│   │   │   ├── models/         # SQLAlchemy DB models (user_model, inventory_model)
│   │   │   ├── repositories/   # DB and Storage query implementations
│   │   ├── use_cases/          # Application-specific logic
│   │   ├── presentation/       # API router, request schemas, middlewares
│   │   ├── ai/                 # AI model wrapper classes (YOLOv11, EasyOCR, ByteTrack)
│   │   └── main.py             # App entrypoint
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── app/                    # Next.js pages, layouts, and global styles
│   ├── components/             # Theme interfaces (Tailwind styling)
│   ├── lib/                    # API client utilities
│   ├── tsconfig.json           # Path-alias configurations
│   └── Dockerfile
│
├── docker-compose.yml          # Container orchestration (FastAPI, Next.js, Postgres)
└── README.md
```

---

## Configuration & Environment Setup

### Environment Variables
Both services use environment templates to configure storage backends, database variables, and JWT parameters. 

#### Backend (`backend/.env`)
Copy `backend/.env.example` to `backend/.env` and adjust the variables:
```bash
# Storage providers: "local", "s3", or "supabase"
STORAGE_PROVIDER=local
LOCAL_STORAGE_DIR=/app/local_storage

# AWS Configs (if provider=s3)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1
AWS_BUCKET_NAME=your-s3-bucket

# Database Configurations
DB_HOST=db
DB_PORT=5432
DB_NAME=grocery_db
DB_USER=postgres
DB_PASSWORD=postgres

# Secret Key (required for JWT tokens)
JWT_SECRET=supersecretjwtkeyforgroceryinventorysystem
```

#### Frontend (`frontend/.env.local`)
Define the URL pointing to the FastAPI gateway:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Getting Started

You can run the entire system using Docker Compose or configure each app manually:

### Option A: Running with Docker Compose (Recommended)
Launch the database, API server, and web dashboard instantly:
```bash
docker compose up --build
```
* **Web Dashboard**: `http://localhost:3000`
* **Backend API Gateway**: `http://localhost:8000`
* **Swagger Documentation**: `http://localhost:8000/docs`

### Option B: Local Manual Start

#### 1. Start Postgres Database
Ensure you have a PostgreSQL server running locally and create a database named `grocery_db`.

#### 2. Start Backend API
```bash
cd backend
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### 3. Start Frontend Dashboard
```bash
cd frontend
npm install
npm run dev
```

---

## Core API Specification

| Endpoint | Method | Security | Description |
| :--- | :--- | :--- | :--- |
| `/api/v1/auth/register` | `POST` | Public | Sign up a new user account |
| `/api/v1/auth/login` | `POST` | Public | Log in, returns a bearer JWT token |
| `/api/v1/auth/me` | `GET` | Bearer Token | Fetch the profile data of the current user |
| `/api/v1/inventory` | `GET` | Bearer Token | Retrieve list of inventory products |
| `/api/v1/inventory` | `POST` | Bearer Token | Manually add a product to inventory |
| `/api/v1/inventory/{id}` | `GET`/`PUT`/`DELETE` | Bearer Token | Retrieve, modify, or delete a product |
| `/api/v1/inventory/scan` | `POST` | Bearer Token | Upload image scan (processes YOLO, Expiry OCR, and tracks via ByteTrack) |
