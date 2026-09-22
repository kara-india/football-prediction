from fastapi import FastAPI
import uvicorn

app = FastAPI(title='Football Prediction Engine', version='0.1.0')

@app.get('/health')
async def health():
    return {'status': 'ok', 'version': '0.1.0'}

@app.post('/analyze/{match_id}')
async def analyze_match(match_id: int):
    # Run full analysis pipeline for match
    return {'status': 'not_implemented', 'match_id': match_id}

@app.get('/providers/status')
async def provider_status():
    # Run health checks on all providers
    return {'providers': []}

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8001)
