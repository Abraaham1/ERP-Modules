-- Runs once on first container start (docker-entrypoint-initdb.d).
-- Creates a separate database per microservice, matching the
-- "separate DBs" requirement in the ERP Modules spec.

CREATE DATABASE auth_db;
CREATE DATABASE attendance_db;
CREATE DATABASE payroll_db;

GRANT ALL PRIVILEGES ON DATABASE auth_db TO CURRENT_USER;
GRANT ALL PRIVILEGES ON DATABASE attendance_db TO CURRENT_USER;
GRANT ALL PRIVILEGES ON DATABASE payroll_db TO CURRENT_USER;
