import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from supabase import create_client
from dotenv import load_dotenv

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "supabase_demo_secret_key"

# Initialize Supabase client
SUPABASE_URL = "https://yiitlhperoytdlyegqre.supabase.co"
# שימוש ב-service role key במקום anon key לאפשר פעולות מנהל
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlpaXRsaHBlcm95dGRseWVncXJlIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0Mzg2MjEzNywiZXhwIjoyMDU5NDM4MTM3fQ.2gPddAbLh6iJOQ7K5REx-O9E95g2KHQnZBq25ocWBQk"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Ensure the users table exists
def initialize_db():
    try:
        # Check if we can connect to the database
        result = supabase.table('users').select('id').limit(1).execute()
        print("Connected to Supabase successfully!")
    except Exception as e:
        print(f"Error connecting to database: {e}")
        # If table doesn't exist, create it
        try:
            # Note: This is simplified - in production, you would use migrations
            # or SQL scripts through Supabase directly rather than this approach
            print("Attempting to create users table...")
            # קריאת קובץ ה-SQL והרצה שלו
            with open('sql_setup.sql', 'r', encoding='utf-8') as f:
                sql = f.read()
                
            # ניסיון להריץ את ה-SQL דרך REST API
            # (הערה: זה עלול לא לעבוד בגלל מגבלות של ה-API)
            try:
                from postgrest.types import Json
                result = supabase.rpc('pg_execute', {'sql': sql}).execute()
                print("Users table created successfully via RPC!")
            except Exception as sql_error:
                print(f"Could not create table via RPC: {sql_error}")
                print("Please create the users table in Supabase dashboard with the following columns:")
                print("- id (auto-incrementing primary key)")
                print("- full_name (text)")
                print("- email (text)")
                print("- created_at (timestamp with time zone)")
        except Exception as e:
            print(f"Error creating table: {e}")

@app.route('/')
def index():
    success_message = request.args.get('success_message', '')
    search_query = request.args.get('search', '')
    
    try:
        if search_query:
            # Search for users matching the query
            response = supabase.table('users').select('*').or_(
                f"full_name.ilike.%{search_query}%,email.ilike.%{search_query}%"
            ).execute()
        else:
            # Get all users
            response = supabase.table('users').select('*').order('created_at', desc=True).execute()
        
        users = response.data
        db_connected = True
    except Exception as e:
        print(f"Error fetching users: {e}")
        users = []
        db_connected = False
        
    return render_template('index.html', 
                          users=users, 
                          success_message=success_message, 
                          search_query=search_query,
                          db_connected=db_connected)

@app.route('/add_user', methods=['POST'])
def add_user():
    full_name = request.form.get('full_name')
    email = request.form.get('email')
    
    if not full_name or not email:
        flash('שם מלא ואימייל הם שדות חובה.')
        return redirect(url_for('index'))
    
    try:
        # Add new user to the database
        now = datetime.now().isoformat()
        new_user = {
            'full_name': full_name,
            'email': email,
            'created_at': now
        }
        
        response = supabase.table('users').insert(new_user).execute()
        
        success_message = f"המשתמש {full_name} נוסף בהצלחה!"
        return redirect(url_for('index', success_message=success_message))
    
    except Exception as e:
        flash(f'שגיאה בהוספת משתמש: {str(e)}')
        return redirect(url_for('index'))

@app.route('/check_connection')
def check_connection():
    try:
        # Try to make a simple query to check connection
        result = supabase.table('users').select('id').limit(1).execute()
        return jsonify({"connected": True, "message": "מחובר לבסיס הנתונים Supabase בהצלחה!"})
    except Exception as e:
        return jsonify({"connected": False, "message": f"שגיאה בחיבור לבסיס הנתונים: {str(e)}"})

# Initialize the database when the app starts
initialize_db()

if __name__ == '__main__':
    # מאזין על כל הממשקים כדי שהאפליקציה תהיה נגישה מבחוץ
    app.run(debug=True, host='0.0.0.0') 