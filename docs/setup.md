# Local Setup Instructions

## Prerequisites
- Node.js 20+
- Python 3.11+
- Git

## Steps
1. Clone the repository: `git clone <repo>`
2. Install frontend dependencies: `npm install`
3. Install Python dependencies: `pip install -r python/requirements.txt`
4. Copy environment template: `cp .env.example .env.local`
5. Set required environment variables in `.env.local`
6. Start development server: `npm run dev`
7. (Optional) Run the local engine: `python python/main.py`

## How to check Supabase connection
Run the local FastAPI server and check the health endpoint or query Supabase directly via its URL.

## How to run tests
Run `make test` or `pytest tests/` for Python and `npm run test` (if set) for TS.
