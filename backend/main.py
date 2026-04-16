from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime
import os
import db

app = FastAPI(title="Transport Vehicle App API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Optional: Run this if database initialization is needed at startup
db.init_db()

class LoginRequest(BaseModel):
    username: str
    password: str

class SignupRequest(BaseModel):
    username: str
    role: str
    password: str

@app.post("/api/login")
async def login(req: LoginRequest):
    # Dummy authentication for initial setup
    if req.username and req.password:
        role = "manager" # Assign dynamically based on user in a real app
        if req.username == "supervisor":
            role = "supervisor"
        elif req.username == "accountant":
            role = "accounting_incharge"
        elif req.username == "operator":
            role = "computer_operator"
            
        return {"status": "success", "message": "Login successful", "role": role}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/api/signup")
async def signup(req: SignupRequest):
    # Dummy signup for initial setup
    if req.username and req.password and req.role:
        return {"status": "success", "message": "Signup successful"}
    raise HTTPException(status_code=400, detail="Missing fields")

class PunchRequest(BaseModel):
    username: str
    location: str
    action: str
    image: str = None

@app.post("/api/attendance")
async def handle_attendance(req: PunchRequest):
    print(f"DEBUG: Received {req.action} request for user {req.username}")
    conn = db.get_db_connection()
    if not conn:
        print("DEBUG: Database connection failed")
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        now = datetime.now()
        
        if req.action == "in":
            print(f"DEBUG: Attempting Punch In for {req.username}")
            # Check if there is already an open punch-in
            cursor.execute("SELECT id FROM attendance WHERE username = %s AND punch_out IS NULL", (req.username,))
            existing = cursor.fetchone()
            if existing:
                print(f"DEBUG: Already punched in (ID: {existing['id']})")
                return {"status": "error", "message": "You are already punched in."}
            
            cursor.execute(
                "INSERT INTO attendance (username, punch_in, location, image_in) VALUES (%s, %s, %s, %s)",
                (req.username, now, req.location, req.image)
            )
            conn.commit()
            print(f"DEBUG: Punch In successful for {req.username}")
            return {"status": "success", "message": f"Punched in at {now.strftime('%H:%M:%S')} with selfie"}
            
        elif req.action == "out":
            # Find the latest open punch-in
            cursor.execute(
                "SELECT id FROM attendance WHERE username = %s AND punch_out IS NULL ORDER BY punch_in DESC LIMIT 1",
                (req.username,)
            )
            record = cursor.fetchone()
            if not record:
                return {"status": "error", "message": "No active punch-in found."}
            
            cursor.execute(
                "UPDATE attendance SET punch_out = %s, image_out = %s WHERE id = %s",
                (now, req.image, record['id'])
            )
            conn.commit()
            return {"status": "success", "message": f"Punched out at {now.strftime('%H:%M:%S')} with selfie"}
            
    except Exception as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database operation failed")
    finally:
        cursor.close()
        conn.close()
    
    raise HTTPException(status_code=400, detail="Invalid action")

@app.get("/api/attendance/history")
async def get_attendance_history(username: str):
    conn = db.get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        # Get last 10 records for the user
        cursor.execute(
            "SELECT punch_in, punch_out, location, image_in, image_out FROM attendance WHERE username = %s ORDER BY punch_in DESC LIMIT 10",
            (username,)
        )
        records = cursor.fetchall()
        
        # Format dates for frontend
        for r in records:
            if r['punch_in']:
                r['punch_in'] = r['punch_in'].strftime("%Y-%m-%d %H:%M:%S")
            if r['punch_out']:
                r['punch_out'] = r['punch_out'].strftime("%Y-%m-%d %H:%M:%S")
                
        return {"status": "success", "history": records}
    except Exception as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch history")
    finally:
        cursor.close()
        conn.close()

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    # Return dummy data for frontend rendering
    return {
        "leaves_balance": {"total": 30, "used": 12, "remaining": 18},
        "pending_vehicles": 5,
        "daily_spending": 2400
    }

# Serve frontend static files
# Construct absolute paths to avoid directory resolution errors regardless of where script is run
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
assets_dir = os.path.join(base_dir, "assets")
frontend_dir = os.path.join(base_dir, "frontend")

try:
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
except RuntimeError as e:
    print(f"Error mounting static files: {e}. Ensure that the 'assets' and 'frontend' directories exist in {base_dir}")

if __name__ == "__main__":
    import uvicorn
    # Make sure to run from the backend directory
    uvicorn.run(app, host="127.0.0.1", port=8001)
