# Grocery Inventory System - Entity Relationship Diagram

This document contains the Entity Relationship (ER) diagram for the system's database schema, modeling 11 normalized tables optimized for millions of records.

```mermaid
erDiagram
    users {
        int id PK
        string email UK
        string hashed_password
        string full_name
        string role
        boolean is_verified
        string verification_token
        string reset_token
        datetime reset_token_expires
        datetime created_at
        datetime updated_at
    }

    stores {
        int id PK
        string name
        string location
        datetime created_at
        datetime updated_at
    }

    user_store_assignments {
        int user_id FK
        int store_id FK
        datetime assigned_at
    }

    products {
        int id PK
        string name
        string barcode UK
        string sku UK
        string category
        text description
        datetime created_at
        datetime updated_at
    }

    inventory_items {
        int id PK
        int store_id FK
        int product_id FK
        string name
        string sku UK
        int quantity
        date expiry_date
        float confidence
        string image_url
        string location_bin
        string status
        datetime created_at
        datetime updated_at
    }

    suppliers {
        int id PK
        string name
        string contact_email
        string phone
        text address
        datetime created_at
        datetime updated_at
    }

    videos {
        int id PK
        int store_id FK
        string camera_name
        string video_url
        string status
        datetime processed_at
        datetime created_at
        datetime updated_at
    }

    ai_scans {
        int id PK
        int video_id FK
        int store_id FK
        int scanned_by_id FK
        string image_url
        string status
        datetime created_at
        datetime updated_at
    }

    ai_scan_detections {
        int id PK
        int scan_id FK
        int product_id FK
        float confidence
        jsonb bounding_box
        date expiry_date_detected
        text raw_ocr_text
        datetime created_at
    }

    reports {
        int id PK
        int store_id FK
        int generated_by_id FK
        string type
        string file_url
        jsonb parameters
        datetime created_at
    }

    orders {
        int id PK
        int store_id FK
        int supplier_id FK
        int created_by_id FK
        string status
        decimal total_amount
        datetime created_at
        datetime updated_at
    }

    order_items {
        int id PK
        int order_id FK
        int product_id FK
        int quantity
        decimal unit_price
    }

    notifications {
        int id PK
        int user_id FK
        int store_id FK
        string title
        text message
        string type
        boolean is_read
        datetime created_at
    }

    audit_logs {
        int id PK
        int user_id FK
        string action
        string table_name
        int record_id
        jsonb payload
        string ip_address
        datetime created_at
    }

    refresh_tokens {
        int id PK
        string token UK
        int user_id FK
        datetime expires_at
        boolean is_revoked
        datetime created_at
    }

    users ||--o{ user_store_assignments : has
    stores ||--o{ user_store_assignments : assigned
    stores ||--o{ inventory_items : has
    products ||--o{ inventory_items : tracks
    stores ||--o{ videos : monitors
    videos ||--o{ ai_scans : scans
    stores ||--o{ ai_scans : scanned_at
    users ||--o{ ai_scans : scanned_by
    ai_scans ||--o{ ai_scan_detections : contains
    products ||--o{ ai_scan_detections : detects
    stores ||--o{ reports : generates
    users ||--o{ reports : generated_by
    stores ||--o{ orders : places
    suppliers ||--o{ orders : supplies
    users ||--o{ orders : created_by
    orders ||--o{ order_items : contains
    products ||--o{ order_items : ordered
    users ||--o{ notifications : receives
    stores ||--o{ notifications : alerts
    users ||--o{ audit_logs : logs
    users ||--o{ refresh_tokens : owns
```
