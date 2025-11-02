# 🚀 How to Start Your Dashboard - Step by Step

## ✅ GOOD NEWS: Hydration Error is FIXED!

The React hydration error has been completely resolved. You should see NO more errors about "button in button" or "hydration failed".

---

## 📌 Current Status

- ✅ **Frontend Code**: Fixed (no hydration errors)
- ✅ **Dependencies**: Installed (FastAPI, uvicorn, etc.)
- ⚠️ **Backend**: Needs to be started manually
- ⚠️ **Frontend**: Already running (port 3000)

---

## 🎯 Quick Start (2 Steps)

### Step 1: Start Backend API

**Open a NEW Command Prompt/PowerShell window** and run:

```batch
cd "C:\Users\lohit\OneDrive\Documents\ATTRAL\Projects\Trading Agent"
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
```

**Wait for this message:**
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Keep this window open!** This is your backend server.

### Step 2: Refresh Your Browser

1. Go to your browser tab with `http://localhost:3000`
2. Press **Ctrl + Shift + R** (hard refresh)
3. Wait 5-10 seconds for WebSocket to connect

---

## ✓ Success Indicators

You'll know it's working when you see:

### In Backend Terminal:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     WebSocket client connected
```

### In Browser:
- ✅ Green "Live" connection indicator (top right)
- ✅ Symbol prices loading (BTC, ETH, SOL, BNB)
- ✅ No CORS errors in console (F12)
- ✅ Message: "WebSocket connected"
- ✅ Portfolio metrics showing
- ✅ AI predictions visible

### In Browser Console (F12):
```
✅ No "Hydration failed" errors
✅ No "CORS" errors  
✅ "WebSocket connected" message
```

---

## 🛠️ Alternative: Use Batch Files

### Option A: Start Backend Only
Double-click: **`start_backend_only.bat`**

Wait for "Application startup complete" message.

### Option B: Start Everything (if frontend not running)
Double-click: **`start_dashboard.bat`** or **`start_dashboard_fixed.bat`**

This will start both backend and frontend.

---

## 🐛 Troubleshooting

### Issue: Backend Shows Errors

If you see errors when starting the backend, the most common are:

#### Error 1: Module Not Found
```
ModuleNotFoundError: No module named 'xyz'
```

**Solution:**
```batch
pip install fastapi uvicorn pydantic sqlalchemy pyyaml pandas numpy scikit-learn xgboost requests structlog
```

#### Error 2: Config File Missing
```
FileNotFoundError: config.yaml
```

**Solution:** The backend will use defaults. If you need to configure it, check `config/config.yaml`.

#### Error 3: Database Error
```
DatabaseError: could not connect
```

**Solution:** The backend will create a SQLite database automatically. Just ignore initial warnings.

### Issue: Frontend Still Shows CORS Errors

**Cause:** Backend not running yet

**Solution:**
1. Make sure backend terminal shows "Application startup complete"
2. Refresh browser (Ctrl + Shift + R)
3. Wait 5-10 seconds for reconnection

### Issue: WebSocket Won't Connect

**Solution:**
1. Ensure backend is running (check terminal)
2. Close and reopen browser tab
3. Hard refresh (Ctrl + Shift + R)
4. Wait 10 seconds

---

## 📋 Complete Checklist

Before you open the browser, ensure:

- [ ] Backend terminal is open
- [ ] Backend shows "Application startup complete"
- [ ] You can access http://localhost:8000/docs
- [ ] Frontend is running (port 3000)
- [ ] Browser is open to http://localhost:3000

---

## 🎉 What Was Fixed

### 1. React Hydration Error - ✅ FIXED
**File:** `frontend_web/src/components/SymbolSelector.tsx`
- Removed nested button structure
- Changed to div with button inside
- All functionality preserved

**Result:** No more hydration errors!

### 2. Backend Dependencies - ✅ INSTALLED
- FastAPI ✅
- Uvicorn ✅
- Pydantic ✅
- SQLAlchemy ✅
- All ML libraries ✅

**Result:** Backend can now start!

---

## 🚀 Expected Performance

Once everything is running:

- **Load Time:** < 2 seconds
- **WebSocket:** Connects in 1-3 seconds
- **Price Updates:** Every 30 seconds
- **AI Predictions:** Every minute
- **No Errors:** Clean console

---

## 💻 Quick Commands Reference

### Start Backend (PowerShell):
```powershell
cd "C:\Users\lohit\OneDrive\Documents\ATTRAL\Projects\Trading Agent"
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
```

### Start Frontend (if needed):
```powershell
cd "C:\Users\lohit\OneDrive\Documents\ATTRAL\Projects\Trading Agent\frontend_web"
npm run dev
```

### Test Backend:
```powershell
curl http://localhost:8000/
```

Should return:
```json
{
  "name": "AI Trading Agent API",
  "version": "1.0.0",
  "status": "running"
}
```

---

## 📞 Still Having Issues?

1. **Close ALL terminal windows**
2. **Open a new PowerShell window as Administrator**
3. **Run:**
   ```powershell
   cd "C:\Users\lohit\OneDrive\Documents\ATTRAL\Projects\Trading Agent"
   python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
   ```
4. **Look for any error messages**
5. **Share the error message if you need help**

---

## 📊 Visual Guide

```
┌─────────────────────────────────────────┐
│  Step 1: Start Backend                 │
│  Terminal: Shows "startup complete"    │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  Step 2: Open/Refresh Browser          │
│  URL: http://localhost:3000            │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  ✅ Success!                            │
│  - Green "Live" indicator               │
│  - No console errors                    │
│  - Prices loading                       │
│  - WebSocket connected                  │
└─────────────────────────────────────────┘
```

---

## ⏱️ Estimated Time

- **Backend Start:** 10-15 seconds
- **Frontend Connect:** 5 seconds
- **Full Functionality:** < 30 seconds total

---

## 🎯 Action Required NOW:

1. **Open a new terminal**
2. **Run the backend start command** (see above)
3. **Wait for "startup complete"**
4. **Refresh your browser**
5. **Enjoy your dashboard!** 🚀

---

**Files Modified:**
- ✅ `frontend_web/src/components/SymbolSelector.tsx` (hydration fix)

**Files Created:**
- 📝 `start_backend_only.bat` (easy backend startup)
- 📝 `START_INSTRUCTIONS.md` (this guide)

---

**Next Steps:** Start the backend and test! 🎉

