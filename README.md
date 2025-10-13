# VLAN Flask API

A serverless Flask API for managing game server instances on AWS, deployed via the Serverless Framework.

## Overview

This application provides HTTP endpoints to control AWS Auto Scaling Groups that manage game server EC2 instances. Users can start and stop game servers on demand through a Firebase-authenticated API.

## Features

- **Game Server Management**: Start/stop game server instances via Auto Scaling Groups
- **Firebase Authentication**: Secure endpoints with Firebase ID token verification
- **Game Listing**: Query available games and server types
- **State Tracking**: Sync game states between AWS and Firebase Firestore
- **Custom Domain**: Deployed at `api.itisamystery.com`

## Prerequisites

- Node.js >= 18.0.0
- Python 3.12
- AWS Account with appropriate permissions
- Firebase project with Admin SDK credentials
- Serverless Framework CLI

## Installation

```bash
npm install
```

## Configuration

### AWS SSM Parameters

The application requires two SSM parameters in the us-west-2 region:

1. **asg_names**: JSON mapping of game names to Auto Scaling Group names
   ```json
   {
     "game1": {
       "type1": "asg-name-1",
       "type2": "asg-name-2"
     },
     "game2": {
       "type1": "asg-name-3"
     }
   }
   ```

2. **firebase_secrets** (encrypted): Firebase service account credentials JSON

### IAM Role

The Lambda function uses the IAM role: `arn:aws:iam::456410706824:role/vlan-flask-sls`

Required permissions:
- `autoscaling:DescribeAutoScalingGroups`
- `autoscaling:SetDesiredCapacity`
- `ec2:DescribeInstances`
- `ssm:GetParameter` (with decryption)

## API Endpoints

### GET /

Health check endpoint.

**Response:**
```json
{
  "yay?": "yay!"
}
```

### POST /game

Start or stop a game server instance.

**Headers:**
```
Authorization: Bearer <firebase-id-token>
```

**Request Body:**
```json
{
  "game": "game1",
  "gameType": "type1",
  "action": "start"
}
```

**Response:**
```json
{
  "success": true,
  "errorMsg": null
}
```

### GET /allGames

List all available games and their types.

**Response:**
```json
{
  "game1": ["type1", "type2"],
  "game2": ["type1"]
}
```

## Development

### Deploy to AWS

```bash
npm run deploy
```

### View Logs

```bash
npm run logs
```

### Get Deployment Info

```bash
npm run info
```

### Local Testing

```bash
serverless wsgi serve
```

### Remove Deployment

```bash
npm run remove
```

## Architecture

- **Runtime**: Python 3.12 on AWS Lambda
- **API Gateway**: HTTP API with CORS enabled
- **Memory**: 256 MB
- **Timeout**: 30 seconds
- **Region**: us-west-2
- **Stage**: prod

## Dependencies

- Flask >= 3.0.0
- boto3 >= 1.28.0
- flask_cors >= 4.0.0
- firebase-admin >= 6.0.0

## Serverless Plugins

- **serverless-wsgi**: WSGI adapter for Flask on Lambda
- **serverless-python-requirements**: Packages Python dependencies
- **serverless-domain-manager**: Custom domain management

## License

Proprietary
