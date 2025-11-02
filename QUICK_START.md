# 🚀 Quick Start Guide - Malaysia Swimming Analytics

## ⚡ Fast Startup (2 Terminals Required)

### Terminal 1: Backend
```bash
cd "C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics"
uvicorn src.web.main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2: Frontend
```bash
cd "C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics"
npm run dev
```

## 🌐 Access Points
- **Frontend**: http://localhost:3000 (or http://localhost:3001)
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs
- **Admin Panel**: http://localhost:3000/admin

## 🔄 Restarting Servers

**To restart backend**: 
- Press `Ctrl+C` in Terminal 1 to stop
- Run the `uvicorn` command again

**To restart frontend**:
- Press `Ctrl+C` in Terminal 2 to stop
- Run `npm run dev` again

## 📊 Current Setup
- **Backend**: FastAPI with SQLite (`malaysia_swimming.db` in project root)
- **Frontend**: Next.js (React)
- **Database Location**: `C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics\malaysia_swimming.db`

## ✅ Features Available
- Database landing page with meet/event filtering
- Admin panel with meet upload and management
- PDF generation for meet results
- Manual result entry
- Meet alias management

## 🆘 Troubleshooting

**Backend won't start?**
- Check for syntax errors: `python -m py_compile src/web/routers/admin.py`
- Make sure port 8000 is not in use
- Check database exists at project root

**Frontend won't start?**
- Run `npm install` if dependencies missing
- Check port 3000/3001 availability
- Clear `.next` cache if needed: `rm -rf .next` (or delete folder on Windows)

**Database issues?**
- Database is at: `malaysia_swimming.db` in project root
- Backend automatically finds it
- If missing, upload meets through admin panel


