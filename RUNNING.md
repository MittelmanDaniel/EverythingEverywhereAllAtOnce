# Running Everything Everywhere All at Once

Three pieces run together: the **backend** API, the **frontend** web server, and the **browser extension**.

---

## Backend (FastAPI · Python)

### Setup

```bash
cd backend
uv pip install -r requirements.txt
```

Create a `.env` file in `backend/`:

```env
SECRET_KEY=your-secret-key
ANTHROPIC_API_KEY=your-anthropic-key
BROWSER_USE_API_KEY=your-browser-use-key
COOKIE_ENCRYPTION_KEY=your-encryption-key
CORS_ORIGINS=http://localhost:3000
```

### Run

```bash
uv run uvicorn app.main:app --reload --port 8000
```

API runs at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### Seed demo data (optional)

```bash
uv run python seed_demo.py
```

---

## Frontend (Express · Node)

### Setup

```bash
cd frontend
npm install
```

### Run

```bash
npm start
```

Frontend runs at `http://localhost:3000`.

---

## Browser Extension (TypeScript · Webpack)

### Setup

```bash
cd extension
npm install
```

### Build

```bash
# One-time production build
npm run build

# Watch mode for development
npm run dev
```

Built files are output to `extension/dist/`.

### Load in Chrome

1. Open `chrome://extensions`
2. Enable **Developer mode** (top right)
3. Click **Load unpacked**
4. Select the `extension/dist/` folder

---

## Running Everything Together

Open three terminals:

```bash
# Terminal 1 — backend
cd backend && uv run uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend && npm start

# Terminal 3 — extension (dev watch, optional)
cd extension && npm run dev
```

Then open `http://localhost:3000`.
