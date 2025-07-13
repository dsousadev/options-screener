/**
 * Cloudflare Worker for options data ingest cron job
 * 
 * This worker runs every 30 seconds to trigger the data ingest service.
 * Currently disabled - will be enabled in Phase 2.5
 */

export default {
  async scheduled(event, env, ctx) {
    // TODO: Enable in Phase 2.5
    // For now, just log that the cron would run
    console.log('Data ingest cron triggered at:', new Date().toISOString());
    
    // Example implementation (disabled):
    /*
    const response = await fetch('https://your-api-endpoint/ingest', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${env.API_TOKEN}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        symbols: ['SPY', 'AAPL', 'NVDA'],
        timestamp: new Date().toISOString()
      })
    });
    
    if (!response.ok) {
      throw new Error(`Ingest failed: ${response.status}`);
    }
    
    const result = await response.json();
    console.log('Ingest completed:', result);
    */
  },
  
  async fetch(request, env, ctx) {
    // Manual trigger endpoint
    return new Response('Data ingest worker is ready', {
      status: 200,
      headers: { 'Content-Type': 'text/plain' }
    });
  }
}; 