# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a serverless Flask application deployed on AWS Lambda using the Serverless Framework. The application manages AWS Auto Scaling Groups (ASGs) for game servers, allowing users to start/stop game instances on demand. It integrates with Firebase for authentication and state management.

## Architecture

### Core Components

- **app.py**: Flask application with HTTP API endpoints
  - `/` - Health check endpoint
  - `/game` - POST endpoint to start/stop game servers (requires Firebase auth)
  - `/allGames` - GET endpoint to list all available games

- **asg.py**: ASGDirector class that orchestrates AWS operations
  - Manages AWS Auto Scaling Groups via boto3
  - Reads ASG configuration from AWS SSM Parameter Store (`asg_names` parameter)
  - Integrates with Firebase Firestore to track game state
  - Handles EC2 instance status queries

- **serverless.yml**: Serverless Framework configuration
  - Deploys to AWS Lambda with Python 3.12 runtime
  - Uses HTTP API Gateway (not REST API)
  - Configured with custom domain via serverless-domain-manager plugin
  - IAM role: `arn:aws:iam::456410706824:role/vlan-flask-sls`

### Key Design Patterns

- **Firebase Integration**: Firebase Admin SDK is initialized once per Lambda cold start and reused across invocations
- **AWS SSM Parameters**: Configuration is stored in SSM Parameter Store:
  - `asg_names`: JSON structure mapping game names to ASG names
  - `firebase_secrets`: Encrypted Firebase service account credentials
- **State Management**: Game states are synchronized between AWS ASGs and Firebase Firestore

## Development Commands

### Deploy Application
```bash
npm run deploy
# or
serverless deploy
```

### View Logs
```bash
npm run logs
# or
serverless logs -f app
```

### Get Deployment Info
```bash
npm run info
# or
serverless info
```

### Remove Deployment
```bash
npm run remove
# or
serverless remove
```

### Local Testing
The serverless-wsgi plugin enables local testing:
```bash
serverless wsgi serve
```

## Python Dependencies

Dependencies are managed in requirements.txt:
- flask (>=3.0.0) - Web framework
- boto3 (>=1.28.0) - AWS SDK
- flask_cors (>=4.0.0) - CORS support
- firebase-admin (>=6.0.0) - Firebase integration

The serverless-python-requirements plugin automatically packages these dependencies for Lambda deployment using Docker (on non-Linux systems).

## AWS Configuration

### Required IAM Permissions
The Lambda function requires:
- Auto Scaling: `DescribeAutoScalingGroups`, `SetDesiredCapacity`
- EC2: `DescribeInstances`
- SSM: `GetParameter` (with decryption for firebase_secrets)

### SSM Parameters Expected Format
- `asg_names`: JSON object like `{"game1": {"type1": "asg-name-1", "type2": "asg-name-2"}, "game2": {...}}`
- `firebase_secrets`: JSON containing Firebase service account credentials

## Authentication Flow

1. Client sends request with `Authorization: Bearer <firebase-token>` header
2. Token is verified using Firebase Admin SDK (`auth.verify_id_token()`)
3. If valid, request proceeds; otherwise returns 401 Unauthorized

## Serverless Framework Plugins

- **serverless-wsgi**: Wraps Flask app for Lambda (creates `wsgi_handler.handler`)
- **serverless-python-requirements**: Packages Python dependencies using Docker
- **serverless-domain-manager**: Manages custom domain (api.itisamystery.com)

## Git Workflow

- Main branch for production: `master`
- Use conventional commits when committing changes
- Current branch: `main`
