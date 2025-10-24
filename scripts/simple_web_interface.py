#!/usr/bin/env python3
"""
Simple Web Interface for Malaysia Swimming Analytics
A basic Flask web interface to test the converted data
"""

import sqlite3
import pandas as pd
from flask import Flask, render_template, request, jsonify
import os
from pathlib import Path

app = Flask(__name__)

# Database path
DB_PATH = Path(__file__).parent.parent / "malaysia_swimming.db"

def get_db_connection():
    """Get database connection"""
    return sqlite3.connect(str(DB_PATH))

@app.route('/')
def index():
    """Main dashboard page"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get basic stats
    cursor.execute("SELECT COUNT(*) FROM athletes")
    total_athletes = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM results")
    total_results = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM meets")
    total_meets = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM events")
    total_events = cursor.fetchone()[0]
    
    # Get recent results
    cursor.execute("""
        SELECT a.name, a.gender, a.age, e.distance, e.stroke, r.time_string, r.place, r.aqua_points, m.name as meet_name
        FROM results r 
        JOIN athletes a ON r.athlete_id = a.id 
        JOIN events e ON r.event_id = e.id
        JOIN meets m ON r.meet_id = m.id
        ORDER BY r.created_at DESC 
        LIMIT 10
    """)
    recent_results = cursor.fetchall()
    
    conn.close()
    
    return render_template('index.html', 
                         total_athletes=total_athletes,
                         total_results=total_results,
                         total_meets=total_meets,
                         total_events=total_events,
                         recent_results=recent_results)

@app.route('/search')
def search():
    """Search page"""
    return render_template('search.html')

@app.route('/api/search')
def api_search():
    """API endpoint for search"""
    query = request.args.get('q', '').strip()
    gender = request.args.get('gender', '')
    stroke = request.args.get('stroke', '')
    distance = request.args.get('distance', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Build search query
    where_conditions = []
    params = []
    
    if query:
        where_conditions.append("a.name LIKE ?")
        params.append(f"%{query}%")
    
    if gender:
        where_conditions.append("a.gender = ?")
        params.append(gender)
    
    if stroke:
        where_conditions.append("e.stroke = ?")
        params.append(stroke)
    
    if distance:
        where_conditions.append("e.distance = ?")
        params.append(int(distance))
    
    where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
    
    sql = f"""
        SELECT a.name, a.gender, a.age, e.distance, e.stroke, r.time_string, r.place, r.aqua_points, m.name as meet_name
        FROM results r 
        JOIN athletes a ON r.athlete_id = a.id 
        JOIN events e ON r.event_id = e.id
        JOIN meets m ON r.meet_id = m.id
        WHERE {where_clause}
        ORDER BY r.time_seconds ASC
        LIMIT 50
    """
    
    cursor.execute(sql, params)
    results = cursor.fetchall()
    conn.close()
    
    return jsonify(results)

@app.route('/api/stats')
def api_stats():
    """API endpoint for statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get event distribution
    cursor.execute("""
        SELECT e.distance, e.stroke, e.gender, COUNT(*) as count
        FROM events e
        JOIN results r ON e.id = r.event_id
        GROUP BY e.distance, e.stroke, e.gender
        ORDER BY e.distance, e.stroke, e.gender
    """)
    event_stats = cursor.fetchall()
    
    # Get meet distribution
    cursor.execute("""
        SELECT m.name, m.meet_type, COUNT(*) as result_count
        FROM meets m
        JOIN results r ON m.id = r.meet_id
        GROUP BY m.id, m.name, m.meet_type
        ORDER BY result_count DESC
    """)
    meet_stats = cursor.fetchall()
    
    conn.close()
    
    return jsonify({
        'events': event_stats,
        'meets': meet_stats
    })

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    templates_dir = Path(__file__).parent / 'templates'
    templates_dir.mkdir(exist_ok=True)
    
    print("Starting Malaysia Swimming Analytics Web Interface...")
    print("Access the website at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)


