# Start here (5 minutes)

You will **type code yourself** in the `lab/` folder. Do not open `solution/` until a step fails.

## 1. Start the API

```bash
cd /path/to/cinephiles
ENV=dev .venv/bin/uvicorn main:app --reload
```

Leave this terminal open. In a browser tab, open http://127.0.0.1:8000/movies — you should see JSON (maybe `[]`).

## 2. Install and run your lab app

Open a **second** terminal:

```bash
cd frontend/walkthrough/lab
cp .env.example .env
npm install
npm run dev
```

Open http://localhost:5174 — you should see **"React lab"** and text about the workbook.

## 3. Open the workbook

In Cursor, open:

**`frontend/walkthrough/WORKBOOK.md`**

Do **Step 1** only. Save the file. Look at the browser again. The page must change.

That is the whole loop: edit file → save → browser updates.

When Step 1 works, continue to Step 2 in the workbook. Do not skip ahead.
