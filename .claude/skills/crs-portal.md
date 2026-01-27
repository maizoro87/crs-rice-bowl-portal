# CRS Rice Bowl Portal

## Overview

Opens the CRS Rice Bowl Lenten Almsgiving Portal in Chrome.

## URLs

- **Public Site**: https://ricebowl.up.railway.app/
- **Admin Panel**: https://ricebowl.up.railway.app/admin
- **Admin Login**: username `admin`, password `lent2026`

## Implementation

Open the site in Chrome:

```bash
# Windows
start chrome "https://ricebowl.up.railway.app/"

# Or open admin directly
start chrome "https://ricebowl.up.railway.app/admin"
```

## Quick Actions

When user invokes this skill:
1. Open the public site in Chrome
2. Optionally open the admin panel if requested

```javascript
// Open public site
Bash({ command: 'start chrome "https://ricebowl.up.railway.app/"' })

// Open admin panel
Bash({ command: 'start chrome "https://ricebowl.up.railway.app/admin"' })
```
