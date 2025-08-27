# Application ID Reference

This file contains the real application IDs used in the multi-tenant setup.

## App Configurations

| App Name | App ID | Style | Port |
|----------|--------|-------|------|
| **Blog app** | `213f36bf-7999-43a7-ac4e-959bf166cdc3` | personal, informal, opinion-driven | 3000 |
| **Article app** | `526ee9a4-0ec2-43c6-a463-397466f6cf52` | structured, informative, analytical | 3001 |
| **News app** | `1c0ef354-6d44-43cc-8826-47bc32245497` | timely, factual, event-driven | 3002 |

## Environment Files

- `env.app1` → Blog app (`213f36bf-7999-43a7-ac4e-959bf166cdc3`)
- `env.app2` → Article app (`526ee9a4-0ec2-43c6-a463-397466f6cf52`) 
- `env.app3` → News app (`1c0ef354-6d44-43cc-8826-47bc32245497`)

## Usage

### Start Individual Apps
```bash
npm run start:app1  # Blog app
npm run start:app2  # Article app  
npm run start:app3  # News app
```

### Start All Apps
```bash
npm run start:all
```

### Manual Start
```bash
REACT_APP_ID=213f36bf-7999-43a7-ac4e-959bf166cdc3 PORT=3000 npm start
REACT_APP_ID=526ee9a4-0ec2-43c6-a463-397466f6cf52 PORT=3001 npm start
REACT_APP_ID=1c0ef354-6d44-43cc-8826-47bc32245497 PORT=3002 npm start
```

## URLs

- **Blog app**: http://localhost:3000
- **Article app**: http://localhost:3001
- **News app**: http://localhost:3002

## Data Source

These app IDs come from `ai_search/data/articles_transformed.json` in the "Apps" section.
