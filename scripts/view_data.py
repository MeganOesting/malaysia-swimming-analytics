#!/usr/bin/env python3
"""
Simple data viewer for Malaysia Swimming Analytics
Shows your converted data in a web browser
"""

import sqlite3
import webbrowser
from pathlib import Path
import tempfile
import os

def create_html_report():
    """Create an HTML report of the swimming data"""
    
    # Connect to the database
    db_path = Path(__file__).parent.parent / "malaysia_swimming.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Get statistics
    cursor.execute("SELECT COUNT(*) FROM athletes")
    total_athletes = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM results")
    total_results = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM meets")
    total_meets = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM events")
    total_events = cursor.fetchone()[0]
    
    # Get sample data
    cursor.execute("""
        SELECT a.name, a.gender, a.age, e.distance, e.stroke, r.time_string, r.place, r.aqua_points, m.name as meet_name
        FROM results r 
        JOIN athletes a ON r.athlete_id = a.id 
        JOIN events e ON r.event_id = e.id
        JOIN meets m ON r.meet_id = m.id
        ORDER BY r.time_seconds ASC
        LIMIT 20
    """)
    top_results = cursor.fetchall()
    
    # Get meet information
    cursor.execute("SELECT name, meet_type, meet_date, location FROM meets")
    meets = cursor.fetchall()
    
    # Get event distribution
    cursor.execute("""
        SELECT e.distance, e.stroke, e.gender, COUNT(*) as count
        FROM events e
        JOIN results r ON e.id = r.event_id
        GROUP BY e.distance, e.stroke, e.gender
        ORDER BY e.distance, e.stroke, e.gender
    """)
    event_stats = cursor.fetchall()
    
    conn.close()
    
    # Create HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Malaysia Swimming Analytics - Data Report</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 10px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 2.5em;
                font-weight: 300;
            }}
            .stats {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                padding: 30px;
                background: #f8f9fa;
            }}
            .stat-card {{
                background: white;
                padding: 25px;
                border-radius: 8px;
                text-align: center;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .stat-number {{
                font-size: 2.5em;
                font-weight: bold;
                color: #2a5298;
                margin-bottom: 10px;
            }}
            .stat-label {{
                color: #666;
                font-size: 1.1em;
            }}
            .content {{
                padding: 30px;
            }}
            .section {{
                margin-bottom: 40px;
            }}
            .section h2 {{
                color: #2a5298;
                border-bottom: 3px solid #2a5298;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            th, td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            th {{
                background: #f8f9fa;
                font-weight: 600;
                color: #2a5298;
            }}
            tr:hover {{
                background: #f8f9fa;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏊‍♀️ Malaysia Swimming Analytics</h1>
                <p>Data Conversion Report - {total_athletes} Athletes, {total_results} Results</p>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">{total_athletes}</div>
                    <div class="stat-label">Athletes</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{total_results}</div>
                    <div class="stat-label">Results</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{total_meets}</div>
                    <div class="stat-label">Meets</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{total_events}</div>
                    <div class="stat-label">Events</div>
                </div>
            </div>
            
            <div class="content">
                <div class="section">
                    <h2>🏆 Top 20 Results (Fastest Times)</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Athlete</th>
                                <th>Gender</th>
                                <th>Age</th>
                                <th>Event</th>
                                <th>Time</th>
                                <th>Place</th>
                                <th>Points</th>
                                <th>Meet</th>
                            </tr>
                        </thead>
                        <tbody>
    """
    
    for result in top_results:
        html_content += f"""
                            <tr>
                                <td>{result[0]}</td>
                                <td>{result[1]}</td>
                                <td>{result[2]}y</td>
                                <td>{result[3]}m {result[4]}</td>
                                <td>{result[5]}</td>
                                <td>{result[6]}</td>
                                <td>{result[7]}</td>
                                <td>{result[8]}</td>
                            </tr>
        """
    
    html_content += """
                        </tbody>
                    </table>
                </div>
                
                <div class="section">
                    <h2>🏊‍♂️ Meets Included</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Meet Name</th>
                                <th>Type</th>
                                <th>Date</th>
                                <th>Location</th>
                            </tr>
                        </thead>
                        <tbody>
    """
    
    for meet in meets:
        html_content += f"""
                            <tr>
                                <td>{meet[0]}</td>
                                <td>{meet[1]}</td>
                                <td>{meet[2]}</td>
                                <td>{meet[3]}</td>
                            </tr>
        """
    
    html_content += """
                        </tbody>
                    </table>
                </div>
                
                <div class="section">
                    <h2>📊 Event Distribution</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Distance</th>
                                <th>Stroke</th>
                                <th>Gender</th>
                                <th>Results Count</th>
                            </tr>
                        </thead>
                        <tbody>
    """
    
    for event in event_stats:
        html_content += f"""
                            <tr>
                                <td>{event[0]}m</td>
                                <td>{event[1]}</td>
                                <td>{event[2]}</td>
                                <td>{event[3]}</td>
                            </tr>
        """
    
    html_content += """
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content

def main():
    """Main function to create and open the HTML report"""
    print("Creating data report...")
    
    # Create HTML content
    html_content = create_html_report()
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(html_content)
        temp_file = f.name
    
    # Open in browser
    print(f"Opening report in browser: {temp_file}")
    webbrowser.open(f'file://{temp_file}')
    
    print("✅ Data report opened in your browser!")
    print("This shows all your converted swimming data:")
    print("- Athletes, results, meets, and events")
    print("- Top performing results")
    print("- Meet information")
    print("- Event distribution")

if __name__ == "__main__":
    main()









