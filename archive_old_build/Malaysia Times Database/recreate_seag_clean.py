#!/usr/bin/env python3
"""
Recreate SEAG_2025_ALL.xlsx from Malaysia On Track Times Spreadsheet Workbook (1).xlsx
Reads from "Age Points Applied to SEA AgeAY" sheet and creates clean SEAG file
"""

import pandas as pd
import os
from pathlib import Path

def get_stroke_acronym(stroke_name):
    """Convert stroke names to acronyms used in other workbooks"""
    stroke_mapping = {
        'Freestyle': 'FR',
        'Backstroke': 'BK', 
        'Breaststroke': 'BR',
        'Butterfly': 'FL',
        'Individual Medley': 'IM',
        'Free': 'FR',
        'Back': 'BK',
        'Breast': 'BR',
        'Fly': 'FL',
        'IM': 'IM'
    }
    return stroke_mapping.get(stroke_name, stroke_name)

def split_event_to_distance_stroke(event_str):
    """Split event string into distance and stroke"""
    if pd.isna(event_str) or event_str == '':
        return '', ''
    
    # Common patterns in swimming events
    event_str = str(event_str).strip()
    
    # Extract distance (numbers at the start)
    import re
    distance_match = re.match(r'(\d+)', event_str)
    distance = distance_match.group(1) if distance_match else ''
    
    # Extract stroke (everything after the distance)
    stroke_part = event_str[len(distance):].strip()
    
    # Convert stroke to acronym
    stroke = get_stroke_acronym(stroke_part)
    
    return distance, stroke

def calculate_aqua_points(time_str, distance, stroke, gender):
    """Calculate AQUA points based on time and event"""
    if not time_str or pd.isna(time_str) or time_str == '':
        return ''
    
    try:
        # Convert time to seconds
        time_seconds = convert_time_to_seconds(time_str)
        if time_seconds is None:
            return ''
        
        # AQUA points formula: 1000 * (base_time / actual_time)
        # For now, using a simplified calculation - you may need to adjust based on your specific formula
        # This is a placeholder - you'll need to provide the actual AQUA calculation formula
        
        # Basic AQUA calculation (this needs to be updated with your actual formula)
        if distance and stroke:
            # Placeholder calculation - replace with your actual AQUA formula
            base_time = 60.0  # This should be the base time for the event
            aqua_points = int(1000 * (base_time / time_seconds))
            return str(aqua_points)
        
        return ''
    except Exception:
        return ''

def convert_time_to_seconds(time_str):
    """Convert time string (e.g., '1:23.45') to seconds"""
    if not time_str or pd.isna(time_str):
        return None
    
    try:
        time_str = str(time_str).strip()
        if ':' in time_str:
            # Format: MM:SS.ss or HH:MM:SS.ss
            parts = time_str.split(':')
            if len(parts) == 2:
                minutes, seconds = parts
                return float(minutes) * 60 + float(seconds)
            elif len(parts) == 3:
                hours, minutes, seconds = parts
                return float(hours) * 3600 + float(minutes) * 60 + float(seconds)
        else:
            # Format: SS.ss
            return float(time_str)
    except Exception:
        return None

def recreate_seag_file():
    """Recreate SEAG_2025_ALL.xlsx with proper column structure"""
    
    # Paths
    source_file = Path("Malaysia On Track Times Spreadsheet Workbook (1).xlsx")
    output_file = Path("Meets/SEAG_2025_ALL.xlsx")
    
    print(f"Reading from: {source_file}")
    print(f"Output to: {output_file}")
    
    try:
        # Read the source sheet
        df = pd.read_excel(source_file, sheet_name="Age Points Applied to SEA AgeAY")
        print(f"Source data shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        
        # Display first few rows to understand structure
        print("\nFirst 5 rows:")
        print(df.head())
        
        # Create new dataframe with standard column structure
        new_data = []
        
        for index, row in df.iterrows():
            # Skip empty rows
            if pd.isna(row.iloc[0]) and pd.isna(row.iloc[1]):
                continue
                
            # Extract data according to standard column structure
            # Source: "Age Points Applied to SEA AgeAY" sheet
            # Target: Standard workbook format (B=Gender, C=Distance, D=Stroke, E=Name, F=Birthdate, G=Age, I=Time, M=Place)
            
            # Column B: Gender (M or F) - from source column B
            gender = row.iloc[1] if len(row) > 1 else ''
            
            # Column C: Event (split into Distance and Stroke) - from source column C
            event = row.iloc[2] if len(row) > 2 else ''
            distance, stroke = split_event_to_distance_stroke(event)
            
            # Column D: Age - from source column D
            age = row.iloc[3] if len(row) > 3 else ''
            
            # Column E: Name - from source column E
            name = row.iloc[4] if len(row) > 4 else ''
            
            # Column I: Time - from source column I
            time = row.iloc[8] if len(row) > 8 else ''
            
            # Column M: Place - from source column M
            place = row.iloc[12] if len(row) > 12 else ''
            
            # Only add if we have essential data
            if name and name != '' and not pd.isna(name):
                # Calculate AQUA points based on time and event
                aqua_points = calculate_aqua_points(time, distance, stroke, gender)
                
                new_row = {
                    'A': '',  # Leave blank as requested
                    'B': gender,  # Gender (M/F)
                    'C': distance,  # Distance (from split event)
                    'D': stroke,    # Stroke (from split event)
                    'E': name,      # Name
                    'F': '',        # Birthdate (not needed - age in G)
                    'G': age,       # Age (direct from source)
                    'H': '',        # Additional data
                    'I': time,      # Time
                    'J': '',        # Additional data
                    'K': aqua_points,  # AQUA points (calculated)
                    'L': '',        # Additional data
                    'M': place,     # Place
                    'N': '25.06.2025',  # Meet date (June 25, 2025)
                    'O': '',        # Additional data
                    'P': '',        # Additional data
                    'Q': '',        # Team/State (blank - use alternate lookup)
                    'R': '',        # Age points (not available in source)
                    'S': '',        # Additional data
                    'T': '',        # Additional data
                    'U': '',        # Additional data
                    'V': '',        # Additional data
                    'W': '',        # Additional data
                    'X': '',        # Additional data
                }
                new_data.append(new_row)
        
        # Create new dataframe
        new_df = pd.DataFrame(new_data)
        
        print(f"\nNew data shape: {new_df.shape}")
        print(f"Created {len(new_data)} rows")
        
        # Save to Excel with proper formatting
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            new_df.to_excel(writer, sheet_name='SEAG_2025_ALL', index=False)
            
            # Get the workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['SEAG_2025_ALL']
            
            # Set column headers to match other workbooks
            headers = [
                'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 
                'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X'
            ]
            
            for col_num, header in enumerate(headers, 1):
                worksheet.cell(row=1, column=col_num, value=header)
        
        print(f"\n✅ Successfully created {output_file}")
        print(f"File contains {len(new_data)} rows of data")
        
        # Display sample of created data
        print("\nSample of created data:")
        print(new_df.head(10))
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔄 Recreating SEAG_2025_ALL.xlsx...")
    success = recreate_seag_file()
    
    if success:
        print("\n✅ SEAG file recreation completed successfully!")
    else:
        print("\n❌ SEAG file recreation failed!")
