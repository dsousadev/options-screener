# Cloudflare Worker for Data Ingest

This directory contains the Cloudflare Worker that will handle the data ingest cron job in production.

## Current Status

- **Phase 2**: Worker skeleton created, currently disabled
- **Phase 2.5**: Will be enabled and deployed to Cloudflare

## Deployment Instructions

### Prerequisites

1. Install Wrangler CLI:
   ```bash
   npm install -g wrangler
   ```

2. Login to Cloudflare:
   ```bash
   wrangler login
   ```

### Deployment Steps

1. **Configure environment variables:**
   ```bash
   wrangler secret put API_TOKEN
   ```

2. **Deploy the worker:**
   ```bash
   wrangler deploy
   ```

3. **Set up the cron trigger:**
   ```bash
   wrangler trigger cron "*/30 * * * * *"
   ```

### Environment Variables

- `API_TOKEN`: Authentication token for the ingest API endpoint

### Monitoring

- View logs: `wrangler tail`
- Check status: `wrangler status`

## Development

- Test locally: `wrangler dev`
- Deploy to staging: `wrangler deploy --env staging`

## Notes

- The worker currently logs but doesn't make API calls (disabled for Phase 2)
- Will be enabled in Phase 2.5 when the API endpoint is ready
- Cron runs every 30 seconds to match the local Docker scheduler 