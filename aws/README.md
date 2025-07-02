# AWS Deployment Guide for AI Agent Project

This guide outlines the steps to deploy the AI Agent Project to AWS using services like EC2, RDS, ElastiCache, ECR, ALB, Route 53, and ACM.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [AWS Infrastructure Setup](#aws-infrastructure-setup)
    - [VPC and Subnets](#vpc-and-subnets)
    - [Security Groups](#security-groups)
    - [RDS for PostgreSQL](#rds-for-postgresql)
    - [ElastiCache for Redis](#elasticache-for-redis)
    - [ECR Repositories](#ecr-repositories)
    - [IAM Role for EC2](#iam-role-for-ec2)
    - [EC2 Instance](#ec2-instance)
    - [Application Load Balancer (ALB)](#application-load-balancer-alb)
    - [Route 53 and ACM (Domain & SSL)](#route-53-and-acm-domain--ssl)
3. [Application Deployment](#application-deployment)
    - [Build and Push Docker Images](#build-and-push-docker-images)
    - [Configure EC2 Instance](#configure-ec2-instance)
    - [Run the Application](#run-the-application)
4. [Post-Deployment](#post-deployment)
    - [Verify Deployment](#verify-deployment)
    - [Monitoring and Logging](#monitoring-and-logging)
5. [Security Best Practices](#security-best-practices)
6. [Cost Management](#cost-management)
7. [Troubleshooting](#troubleshooting)

---

## 1. Prerequisites

*   **AWS Account**: An active AWS account with necessary permissions.
*   **AWS CLI**: Configured locally with credentials. ([Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html))
*   **Docker**: Installed locally to build images.
*   **Git**: To clone the project repository.
*   **Domain Name**: A registered domain name (optional, but needed for SSL with ACM).

---

## 2. AWS Infrastructure Setup

It's recommended to create these resources in the same AWS region.

### VPC and Subnets

*   A Virtual Private Cloud (VPC) provides an isolated network environment.
*   Create a VPC (e.g., `ai-agent-vpc`).
*   Create at least two public subnets (for ALB) and two private subnets (for EC2, RDS, ElastiCache) across different Availability Zones (AZs) for high availability.
*   Configure Route Tables:
    *   Public subnets: Route to an Internet Gateway (IGW).
    *   Private subnets: Route to a NAT Gateway (placed in a public subnet) if instances need outbound internet access (e.g., to pull OS updates, connect to OpenAI).

### Security Groups

Security Groups act as virtual firewalls. Create the following:

1.  **ALB Security Group (`sg-alb`)**:
    *   Inbound: Allow HTTP (80) and HTTPS (443) from `0.0.0.0/0`.
    *   Outbound: Allow all traffic to EC2 instance SG.

2.  **EC2 Instance Security Group (`sg-ec2`)**:
    *   Inbound:
        *   Allow HTTP (80) from `sg-alb` (ALB's security group). This is where Nginx gateway in Docker will listen.
        *   Allow SSH (22) from your IP address for management.
    *   Outbound: Allow all traffic (or restrict to necessary endpoints like RDS, ElastiCache, ECR, OpenAI, etc.).

3.  **RDS PostgreSQL Security Group (`sg-rds`)**:
    *   Inbound: Allow PostgreSQL (5432) from `sg-ec2`.
    *   Outbound: (Usually not needed to restrict explicitly).

4.  **ElastiCache Redis Security Group (`sg-elasticache`)**:
    *   Inbound: Allow Redis (6379) from `sg-ec2`.
    *   Outbound: (Usually not needed).

### RDS for PostgreSQL

1.  Go to the AWS RDS console.
2.  Click "Create database".
3.  Choose "Standard Create" and "PostgreSQL".
4.  Select a version (e.g., PostgreSQL 16.x, compatible with pgvector).
5.  Under "Templates", choose "Free tier" for learning/testing, or an appropriate production size (e.g., `db.t3.micro` or `db.t3.small` to start).
6.  **Settings**:
    *   `DB instance identifier`: e.g., `ai-agent-postgres-db`
    *   `Master username`: e.g., `ai_agent_user` (or use value from your `.env.example`)
    *   `Master password`: Set a strong password.
7.  **Connectivity**:
    *   `Virtual Private Cloud (VPC)`: Select your `ai-agent-vpc`.
    *   `Subnet group`: Create a new DB subnet group using your private subnets.
    *   `Public access`: "No".
    *   `VPC security group`: Choose `sg-rds`.
8.  **Database options**:
    *   `Initial database name`: e.g., `ai_agent_db` (or use value from your `.env.example`)
9.  **Backup, Monitoring, Maintenance**: Configure as needed. Start with defaults if unsure.
10. Click "Create database".
11. **Important**: Once created, note down the **Endpoint** and **Port**. This will be your `DATABASE_URL` host and port.
12. **Enable pgvector extension**: After the DB is available, connect to it using a PostgreSQL client (e.g., `psql` or pgAdmin) and run: `CREATE EXTENSION IF NOT EXISTS vector;`

### ElastiCache for Redis

1.  Go to the AWS ElastiCache console.
2.  Click "Create" under Redis clusters.
3.  **Cluster settings**:
    *   `Cluster engine`: Redis.
    *   `Name`: e.g., `ai-agent-redis-cache`
    *   `Node type`: `cache.t3.micro` (Free tier eligible) or suitable size.
    *   `Number of replicas`: 0 for a single node cluster (for learning). For HA, choose 1 or more.
4.  **Connectivity**:
    *   `Subnet group`: Create a new subnet group using your private subnets.
    *   `VPC Security Group(s)`: Choose `sg-elasticache`.
5.  **Advanced Redis settings**:
    *   Enable "Encryption in-transit" if desired (recommended for production).
    *   Enable "Encryption at-rest" if desired.
6.  Click "Create".
7.  **Important**: Once available, note down the **Primary Endpoint**. This will be your `REDIS_HOST`. The port is typically `6379`.

### ECR Repositories

Create ECR repositories for each service that has a Docker image:
*   `ai-agent-backend`
*   `ai-agent-service` (for the AI agent)
*   `ai-agent-frontend` (for the Nginx image serving React build)
*   `ai-agent-nginx-gateway`

Use the AWS ECR console or AWS CLI:
```bash
aws ecr create-repository --repository-name ai-agent-backend --region <your-region>
aws ecr create-repository --repository-name ai-agent-service --region <your-region>
aws ecr create-repository --repository-name ai-agent-frontend --region <your-region>
aws ecr create-repository --repository-name ai-agent-nginx-gateway --region <your-region>
```

### IAM Role for EC2

Create an IAM role that your EC2 instance will assume. This role needs permissions to:
*   Pull images from ECR.
*   (Optional) Write logs to CloudWatch.
*   (Optional) Access other AWS services if needed (e.g., S3 for configuration files).

An example policy (`iam-ec2-policy.json`) is provided in this directory. Attach policies like `AmazonEC2ContainerRegistryReadOnly` and a custom policy for CloudWatch Logs.

### EC2 Instance

1.  Go to the EC2 console and "Launch instances".
2.  **Name**: `ai-agent-server`
3.  **AMI**: Choose "Amazon Linux 2023 AMI" or a recent Ubuntu Server LTS.
4.  **Instance type**: `t3.medium` (as requested) or `t2.medium`. (Consider `t3.micro` or `t2.micro` for cost saving if load is low).
5.  **Key pair**: Create or select an existing key pair to SSH into the instance.
6.  **Network settings**:
    *   `VPC`: Select `ai-agent-vpc`.
    *   `Subnet`: Select one of your **private subnets**. (ALB will be in public, EC2 in private).
    *   `Auto-assign public IP`: "Disable" (Access via ALB or Bastion Host). If you need direct SSH access and don't have a bastion/VPN, you might temporarily enable it or place it in a public subnet for setup, then move to private. For simplicity here, we might assume public subnet for easier initial SSH. *Revising: For ALB setup, EC2 should be in a private subnet if NAT Gateway is configured. If no NAT, public subnet is simpler.* Let's proceed with a **public subnet** for simpler initial SSH access for this guide, but note private is best practice with NAT/Bastion.
    *   `Firewall (security groups)`: Select existing security group: `sg-ec2`.
7.  **Advanced details**:
    *   `IAM instance profile`: Select the IAM role created in the previous step.
    *   **User data**: Copy the content of `aws/ec2-user-data.sh`. This script will install Docker, Docker Compose, and AWS CLI.
8.  **Storage**: Default (e.g., 30GB gp3) is usually fine.
9.  Launch the instance.

### Application Load Balancer (ALB)

1.  Go to EC2 > Load Balancers > "Create Load Balancer".
2.  Choose "Application Load Balancer".
3.  **Basic configuration**:
    *   `Load balancer name`: `ai-agent-alb`
    *   `Scheme`: `Internet-facing`
    *   `IP address type`: `ipv4`
4.  **Network mapping**:
    *   `VPC`: Select `ai-agent-vpc`.
    *   `Mappings`: Select your two **public subnets** (one in each AZ).
5.  **Security groups**: Select `sg-alb`.
6.  **Listeners and routing**:
    *   Default listener: HTTP, Port 80.
    *   Default action: Create a new Target Group.
        *   `Target group name`: `tg-ai-agent-nginx`
        *   `Target type`: `Instances`
        *   `Protocol`: `HTTP`, `Port`: `80` (This is the port Nginx gateway on EC2 listens on)
        *   `VPC`: `ai-agent-vpc`
        *   `Health checks`: Protocol `HTTP`, Path `/nginx_health` (or another health endpoint exposed by your Nginx gateway). Adjust advanced settings as needed (interval, timeout, thresholds).
        *   Register targets: Select your `ai-agent-server` EC2 instance.
7.  (Optional, for HTTPS) Add Listener for HTTPS on Port 443:
    *   `Protocol`: HTTPS, `Port`: 443
    *   `Default SSL certificate`: Choose "From ACM" and select your certificate (see next section).
    *   `Default action`: Forward to `tg-ai-agent-nginx`.
    *   `Security policy`: Use the recommended one (e.g., `ELBSecurityPolicy-2016-08`).
8.  Create the load balancer. Note its **DNS name**.

### Route 53 and ACM (Domain & SSL)

1.  **AWS Certificate Manager (ACM)**:
    *   Request a public certificate for your domain (e.g., `app.yourdomain.com`).
    *   Use DNS validation (easier if your domain is managed by Route 53). ACM will provide CNAME records to add to your DNS.
2.  **Route 53**:
    *   If your domain is managed by Route 53, create CNAME records as prompted by ACM for certificate validation.
    *   Create an 'A' record (Alias) pointing your domain/subdomain (e.g., `app.yourdomain.com`) to the ALB's DNS name.

---

## 3. Application Deployment

### Build and Push Docker Images

For each service (`backend`, `ai-agent`, `frontend`, `nginx_gateway`):

1.  **Login to ECR**:
    ```bash
    aws ecr get-login-password --region <your-region> | docker login --username AWS --password-stdin <your-aws-account-id>.dkr.ecr.<your-region>.amazonaws.com
    ```
2.  **Build the image**: Navigate to the service directory (e.g., `cd backend`)
    ```bash
    # For backend
    docker build -t ai-agent-backend .
    # For ai-agent
    docker build -t ai-agent-service . # In ai-agent/ directory
    # For frontend (builds React app with Nginx)
    docker build -t ai-agent-frontend . # In frontend/ directory
    # For nginx_gateway
    docker build -t ai-agent-nginx-gateway . # In nginx/ directory
    ```
3.  **Tag the image**:
    ```bash
    docker tag ai-agent-backend:latest <your-aws-account-id>.dkr.ecr.<your-region>.amazonaws.com/ai-agent-backend:latest
    docker tag ai-agent-service:latest <your-aws-account-id>.dkr.ecr.<your-region>.amazonaws.com/ai-agent-service:latest
    docker tag ai-agent-frontend:latest <your-aws-account-id>.dkr.ecr.<your-region>.amazonaws.com/ai-agent-frontend:latest
    docker tag ai-agent-nginx-gateway:latest <your-aws-account-id>.dkr.ecr.<your-region>.amazonaws.com/ai-agent-nginx-gateway:latest
    ```
4.  **Push the image**:
    ```bash
    docker push <your-aws-account-id>.dkr.ecr.<your-region>.amazonaws.com/ai-agent-backend:latest
    # Repeat for other images
    ```

### Configure EC2 Instance

1.  **SSH into your EC2 instance**.
2.  **Create Project Directory**:
    ```bash
    mkdir ~/ai-agent-project
    cd ~/ai-agent-project
    ```
3.  **Create `.env` file**:
    *   Copy the content of your local `.env.example` or a prepared production `.env` file.
    *   **Crucially, update the following variables**:
        *   `DATABASE_URL`: `postgresql://<rds_user>:<rds_password>@<rds_endpoint>:<rds_port>/<rds_db_name>`
        *   `REDIS_HOST`: `<elasticache_primary_endpoint>`
        *   `REDIS_PASSWORD`: (If you set one for ElastiCache)
        *   `SECRET_KEY`: A strong, unique secret for JWT.
        *   `OPENAI_API_KEY`: Your OpenAI API key.
        *   Other variables as needed (e.g., `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`).
    *   Example:
        ```ini
        # .env on EC2 instance
        POSTGRES_USER=ai_agent_user # From RDS setup
        POSTGRES_PASSWORD=your_strong_rds_password # From RDS setup
        POSTGRES_DB=ai_agent_db # From RDS setup
        DATABASE_URL=postgresql://ai_agent_user:your_strong_rds_password@ai-agent-postgres-db.<unique-id>.<region>.rds.amazonaws.com:5432/ai_agent_db

        REDIS_HOST=ai-agent-redis-cache.<unique-id>.<region>.cache.amazonaws.com
        REDIS_PORT=6379
        # REDIS_PASSWORD=your_redis_password # If set

        SECRET_KEY=generate_a_very_strong_random_secret_key_for_production
        ALGORITHM=HS256
        ACCESS_TOKEN_EXPIRE_MINUTES=60 # Longer expiry for prod?

        OPENAI_API_KEY=sk-your_openai_api_key_here
        PINECONE_VECTOR_DIMENSION=1536 # For OpenAI embedding dim

        # These are used by docker-compose.prod.yml to tag/pull images correctly
        AWS_ACCOUNT_ID=<your-aws-account-id>
        AWS_REGION=<your-region>
        ECR_REPOSITORY_NAME_BACKEND=ai-agent-backend
        # ... etc for other ECR repos if your compose file uses these for image names (it currently doesn't, images are hardcoded in compose)
        ```
4.  **Copy `docker-compose.prod.yml` to EC2**:
    *   You can use `scp`, copy-paste into `nano` or `vim`, or clone the repo on EC2 and use the file from there.
    *   Ensure image names in `docker-compose.prod.yml` correctly point to your ECR images.
        Example for `backend` service in `docker-compose.prod.yml` if images were not built with ECR path:
        ```yaml
        # services:
        #   backend:
        #     image: <your-aws-account-id>.dkr.ecr.<your-region>.amazonaws.com/ai-agent-backend:latest
        #     # ... rest of backend config ...
        ```
        **Important Modification for `docker-compose.prod.yml`**: Before deploying to EC2, modify your `docker-compose.prod.yml` file. For each service (`backend`, `ai_agent`, `frontend`, `nginx_gateway`), replace the `build:` directive with an `image:` directive pointing to the ECR repository URI for that service's image. Example:
        ```yaml
        # In your local docker-compose.prod.yml, before copying to EC2:
        services:
          backend:
            image: <your-aws-account-id>.dkr.ecr.<your-region>.amazonaws.com/ai-agent-backend:latest
            # Remove build: section for backend
            container_name: ai_agent_backend_service_prod
            command: uvicorn app.main:app --host 0.0.0.0 --port 8000
            # ... rest of backend config ...
          # Repeat for ai_agent, frontend, and nginx_gateway services
        ```
        This ensures Docker Compose pulls pre-built images from ECR instead of trying to build them on the EC2 instance.

### Run the Application

1.  **Login to ECR (on EC2 instance)**:
    The EC2 instance role should grant ECR pull access. The `docker login` step using AWS CLI helps ensure credentials are fresh if needed, though often the instance role is sufficient for `docker compose pull`.
    ```bash
    aws ecr get-login-password --region <your-region> | sudo docker login --username AWS --password-stdin <your-aws-account-id>.dkr.ecr.<your-region>.amazonaws.com
    ```
2.  **Pull images (if `docker-compose.prod.yml` uses `image:` directive):**
    ```bash
    sudo docker compose -f docker-compose.prod.yml pull
    ```
3.  **Start services**:
    ```bash
    sudo docker compose -f docker-compose.prod.yml up -d
    ```
    (The `-f` flag specifies the production compose file. `-d` runs in detached mode.)

---

## 4. Post-Deployment

### Verify Deployment

1.  Access your application via the ALB's DNS name or your configured domain name (e.g., `http://app.yourdomain.com` or `https://app.yourdomain.com`).
2.  Test all functionalities: user registration, login, chat, history.
3.  Check ALB Target Group health checks.
4.  Check Docker container logs on EC2: `sudo docker compose -f docker-compose.prod.yml logs -f <service_name>`

### Monitoring and Logging

*   **CloudWatch Logs**: Configure Docker log driver on EC2 to send container logs to CloudWatch Logs for centralized logging. This requires the EC2 instance role to have `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents` permissions.
    Update `docker-compose.prod.yml` for each service:
    ```yaml
    # logging:
    #   driver: "awslogs"
    #   options:
    #     awslogs-group: "/ecs/ai-agent-project" # Or your preferred log group
    #     awslogs-region: "<your-region>"
    #     awslogs-stream-prefix: "service-name" # e.g., backend, frontend
    ```
*   **CloudWatch Metrics**: Monitor EC2 CPU/Memory/Network, RDS metrics, ElastiCache metrics, ALB request counts/latency/errors.
*   **CloudWatch Alarms**: Set up alarms for critical metrics (e.g., high CPU, low disk space, ALB 5XX errors).
*   **Application-Level Logging**: Ensure applications log useful information. FastAPI and Uvicorn logs are usually sent to stdout/stderr, which Docker captures.

---

## 5. Security Best Practices

*   **Principle of Least Privilege**: IAM roles and Security Groups should only have necessary permissions.
*   **Secrets Management**: Use AWS Secrets Manager or Parameter Store for sensitive data like API keys and database credentials instead of putting them directly in `.env` files on EC2. Inject them into containers as environment variables.
*   **HTTPS**: Enforce HTTPS by configuring SSL/TLS on the ALB. Redirect HTTP to HTTPS.
*   **Regular Updates**: Keep AMIs, OS packages, Docker images, and application dependencies updated.
*   **Web Application Firewall (WAF)**: Consider using AWS WAF with your ALB for protection against common web exploits.
*   **Vulnerability Scanning**: Regularly scan Docker images for vulnerabilities (e.g., using Amazon ECR scanning or third-party tools).
*   **Private Subnets**: Place EC2, RDS, and ElastiCache in private subnets. Use a NAT Gateway for outbound internet if needed. Access EC2 via a Bastion Host or Systems Manager Session Manager.

---

## 6. Cost Management

*   **Right-Sizing**: Choose appropriate instance sizes for EC2, RDS, and ElastiCache based on load. Start small and scale up if needed.
*   **Free Tier**: Utilize AWS Free Tier resources where possible for development and testing.
*   **Reserved Instances/Savings Plans**: For long-running production workloads, consider Reserved Instances or Savings Plans for significant discounts.
*   **Monitoring Costs**: Use AWS Cost Explorer and set up billing alarms.
*   **Stop/Delete Unused Resources**: Shut down or delete resources when not in use, especially for dev/test environments.
*   **Data Transfer Costs**: Be mindful of data transfer costs between AZs and out to the internet.

---

## 7. Troubleshooting

*   **Container Logs**: `sudo docker logs <container_id_or_name>` or `sudo docker compose -f docker-compose.prod.yml logs <service_name>`.
*   **ALB Health Checks**: Check target group health status in the EC2 console.
*   **Security Groups/NACLs**: Ensure they are not blocking traffic.
*   **IAM Permissions**: Verify EC2 instance role has necessary permissions (e.g., ECR pull).
*   **CloudWatch Logs**: Check application and Nginx logs if configured.
*   **Connectivity**: Use `telnet` or `nc` from within the EC2 instance to test connectivity to RDS/ElastiCache endpoints on their respective ports.

---
This guide provides a comprehensive overview. Real-world deployments might require further customization and consideration of specific organizational needs.Okay, the AWS deployment guide `aws/README.md` has been created.

Next, I'll create the `aws/ec2-user-data.sh` script.
