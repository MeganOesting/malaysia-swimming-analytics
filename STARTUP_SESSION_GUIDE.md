# 🚀 Startup Session Guide - Malaysia Swimming Analytics

## **The Challenge: Two Different Tech Stacks**

You're right - the tech stack difference is significant:

- **Legacy**: Flask + pandas + Excel (Python-based)
- **New**: React + FastAPI + PostgreSQL + Docker (Modern web stack)

## **🎯 Recommended Approach: Choose Your Focus**

### **Option 1: Focus on New Build (Recommended)**
**When to use**: Most development sessions, implementing new features

```bash
# Start new build
cd "C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics"
docker-compose up -d

# Access points:
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/api/docs
```

**What you get**:
- Modern React interface (UI foundation complete)
- FastAPI backend (basic endpoints working)
- Docker environment (all services running)
- SQLite database (all data converted)

**What's missing**:
- Filter functionality (UI exists, backend logic needed)
- Age Points calculation (need to port from legacy)
- Export functionality (need to implement)
- Foreign athlete detection (need to port logic)

### **Option 2: Reference Legacy System**
**When to use**: Understanding business logic, debugging, comparing results

```bash
# Start legacy system
cd "C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics\Malaysia Times Database"
python -m Malaysia_Times_Database.Malaysia_Database

# Access at: http://127.0.0.1:5000
```

**What you get**:
- Fully functional system
- All business logic working
- Complete feature set
- Admin debugging tools

### **Option 3: Compare Both Systems**
**When to use**: Validation, testing, porting features

```bash
# Terminal 1: New build
cd "C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics"
docker-compose up -d

# Terminal 2: Legacy system  
cd "C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics\Malaysia Times Database"
python -m Malaysia_Times_Database.Malaysia_Database

# Access both:
# New: http://localhost:3000
# Legacy: http://127.0.0.1:5000
```

## **🎯 Session Type Recommendations**

### **Development Session (Porting Features)**
**Start with**: New build
**Reference**: Legacy system for business logic
**Goal**: Implement missing functionality in new system

**Example workflow**:
1. Start new build: `docker-compose up -d`
2. Open new system: http://localhost:3000
3. Identify missing feature (e.g., Age Points calculation)
4. Check legacy system: http://127.0.0.1:5000
5. Port the logic from Flask to FastAPI
6. Test in new system
7. Compare results with legacy system

### **Debugging Session**
**Start with**: Legacy system (working reference)
**Goal**: Fix issues in new system

**Example workflow**:
1. Start legacy system: `python -m Malaysia_Times_Database.Malaysia_Database`
2. Test functionality in legacy system
3. Identify the correct behavior
4. Start new build: `docker-compose up -d`
5. Implement fix in new system
6. Test both systems produce same results

### **New Feature Session**
**Start with**: New build
**Goal**: Add new functionality

**Example workflow**:
1. Start new build: `docker-compose up -d`
2. Design new feature
3. Implement in React/FastAPI
4. Test thoroughly
5. Deploy to new system

## **📋 Quick Decision Guide**

### **"I want to work on the new system"**
→ **Start with Option 1** (New build)
→ Focus on porting missing features
→ Use legacy system as reference

### **"I need to understand how something works"**
→ **Start with Option 2** (Legacy system)
→ Study the working implementation
→ Then port to new system

### **"I need to test/validate something"**
→ **Start with Option 3** (Both systems)
→ Compare results between systems
→ Ensure feature parity

### **"I'm starting fresh and don't know what to do"**
→ **Start with Option 1** (New build)
→ Explore the modern interface
→ Identify what's missing
→ Use legacy system as reference for implementation

## **🔧 Practical Session Starters**

### **For Most Sessions (CURRENT SETUP - Recommended)**
```bash
# IMPORTANT: Run these in TWO separate terminals!

# Terminal 1: Backend (FastAPI)
cd "C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics"
uvicorn src.web.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend (Next.js)
cd "C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics"
npm run dev

# 3. Access points:
# Frontend: http://localhost:3000 (or http://localhost:3001)
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/api/docs
# Admin Panel: http://localhost:3000/admin (or http://localhost:3001/admin)

# 4. To restart backend: Stop (Ctrl+C) and run the uvicorn command again
# 5. To restart frontend: Stop (Ctrl+C) and run npm run dev again
```

**Current Tech Stack**:
- **Backend**: FastAPI with SQLite database (`malaysia_swimming.db` in project root)
- **Frontend**: Next.js (React) running on port 3000 or 3001
- **Database**: SQLite (not PostgreSQL/Docker - simplified setup)

### **For Legacy Reference Sessions**
```bash
# 1. Start legacy system
cd "C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics\Malaysia Times Database"
python -m Malaysia_Times_Database.Malaysia_Database

# 2. Access legacy system
# http://127.0.0.1:5000

# 3. If you need to work on new system:
# Open new terminal and run:
cd "C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics"
docker-compose up -d
# Access: http://localhost:3000
```

## **🎯 Key Insight: Parallel Development**

The best approach is to **treat them as two separate systems** during development:

- **New system**: Your primary development target
- **Legacy system**: Your reference implementation
- **Goal**: Port all functionality from legacy to new
- **Method**: Feature by feature, testing as you go

## **📊 Current Status Summary**

### **New Build (React/FastAPI)**
- ✅ **UI Foundation**: Complete and locked in
- ✅ **Data Conversion**: All meet files converted to SQLite
- ✅ **Basic API**: Simple data retrieval working
- ✅ **Docker Setup**: All 6 services running
- ❌ **Filter Logic**: UI exists, backend logic missing
- ❌ **Calculations**: Age Points, AQUA, MOT logic missing
- ❌ **Export**: XLSX download not implemented
- ❌ **Admin Tools**: Debugging tools missing

### **Legacy Build (Flask)**
- ✅ **Complete Functionality**: All features working
- ✅ **Business Logic**: Age Points, foreign detection, etc.
- ✅ **Admin Tools**: Full debugging system
- ✅ **Export**: Excel export working
- ✅ **Performance**: Optimized and tested

## **🎯 Next Steps Recommendation**

1. **Start with new build** (React/FastAPI)
2. **Identify missing features** by comparing with legacy
3. **Port functionality piece by piece**
4. **Test each ported feature** against legacy system
5. **Maintain feature parity** throughout development

This approach gives you the best of both worlds: modern architecture with proven business logic.





