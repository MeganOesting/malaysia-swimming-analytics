"""
Match unmatched results against unmatched registrations
Finds potential matches between athletes with results but no registration
and registered athletes with no results
"""

import pandas as pd
import re
from datetime import datetime
from pathlib import Path

# File path
INPUT_FILE = r'C:\Users\megan\Downloads\REMAINING_UNMATCHED_RECORDS964_3815.xlsx'
OUTPUT_FILE = r'C:\Users\megan\Downloads\POTENTIAL_MATCHES.xlsx'

def normalize_name(name):
    """Normalize name for matching: lowercase, remove punctuation"""
    if pd.isna(name):
        return ''
    return re.sub(r'[^a-z\s]', '', str(name).lower()).strip()

def get_name_words(name):
    """Extract words from name"""
    return set(w for w in normalize_name(name).split() if len(w) >= 2)

def levenshtein_distance(s1, s2):
    """Calculate Levenshtein (edit) distance between two strings"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def fuzzy_word_match(word1, word2, max_distance=1):
    """Check if two words are similar (within edit distance)"""
    if word1 == word2:
        return True
    # For short words, require exact match
    if len(word1) < 4 or len(word2) < 4:
        return False
    # For longer words, allow 1 edit (alif/aliff, terance/terence)
    return levenshtein_distance(word1, word2) <= max_distance

def count_matching_words(words1, words2):
    """Count matches including fuzzy matches for spelling variants"""
    exact_matches = words1.intersection(words2)
    fuzzy_matches = set()

    # Find fuzzy matches for non-exact words
    unmatched1 = words1 - exact_matches
    unmatched2 = words2 - exact_matches

    for w1 in unmatched1:
        for w2 in unmatched2:
            if fuzzy_word_match(w1, w2):
                fuzzy_matches.add(w1)
                break  # Only count each word once

    return len(exact_matches), len(fuzzy_matches), exact_matches, fuzzy_matches

def normalize_date(date_val):
    """Normalize date to YYYY-MM-DD string"""
    if pd.isna(date_val):
        return None
    try:
        if hasattr(date_val, 'strftime'):
            return date_val.strftime('%Y-%m-%d')
        # Try parsing string dates
        date_str = str(date_val).strip()
        for fmt in ['%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y', '%m/%d/%Y']:
            try:
                dt = datetime.strptime(date_str[:10], fmt)
                return dt.strftime('%Y-%m-%d')
            except:
                continue
    except:
        pass
    return None

def main():
    print("Loading data...")
    df = pd.read_excel(INPUT_FILE)

    # Split into results and registrations
    results = df[df['_match_category'] == 'leftover_result'].copy()
    regs = df[df['_match_category'] == 'leftover_registration'].copy()

    print(f'Results to match: {len(results)}')
    print(f'Registrations available: {len(regs)}')

    # Build registration lookup by name words
    # Include ALL name fields: First, Last, Middle, Suffix, Preferred Name
    print('\nBuilding registration index...')
    reg_index = {}
    reg_by_bday = {}

    for idx, row in regs.iterrows():
        # Collect ALL name fields for comprehensive matching
        name_fields = [
            str(row.get('reg_Memb. First Name', '') or ''),
            str(row.get('reg_Memb. Last Name', '') or ''),
            str(row.get('reg_Memb. Middle Initial', '') or ''),
            str(row.get('reg_Memb. Suffix', '') or ''),
            str(row.get('reg_Preferred Name', '') or ''),
        ]
        full = ' '.join(name_fields)
        words = get_name_words(full)

        # Index by name words
        for word in words:
            if len(word) >= 3:
                if word not in reg_index:
                    reg_index[word] = []
                reg_index[word].append(idx)

        # Index by birthdate
        bday = normalize_date(row.get('reg_Birthday'))
        if bday:
            if bday not in reg_by_bday:
                reg_by_bday[bday] = []
            reg_by_bday[bday].append(idx)

    print(f'Index has {len(reg_index)} unique name words')
    print(f'Index has {len(reg_by_bday)} unique birthdates')

    # Try to match each result
    matches = []
    no_match = []

    for ridx, rrow in results.iterrows():
        result_name = str(rrow.get('FULLNAME', '') or '')
        result_words = get_name_words(result_name)
        result_bday = normalize_date(rrow.get('BIRTHDATE'))
        result_gender = str(rrow.get('GENDER', '') or '').upper()[:1]
        result_club = str(rrow.get('CLUBNAME', '') or '')
        result_nation = str(rrow.get('NATION', '') or '')

        # Find candidate registrations by name words
        candidates = set()
        for word in result_words:
            if word in reg_index:
                candidates.update(reg_index[word])

        # Also add candidates by birthdate
        if result_bday and result_bday in reg_by_bday:
            candidates.update(reg_by_bday[result_bday])

        # Score candidates
        best_match = None
        best_score = 0
        best_reason = ''

        for cidx in candidates:
            crow = regs.loc[cidx]
            # Use ALL name fields for matching (same as index building)
            reg_name_fields = [
                str(crow.get('reg_Memb. First Name', '') or ''),
                str(crow.get('reg_Memb. Last Name', '') or ''),
                str(crow.get('reg_Memb. Middle Initial', '') or ''),
                str(crow.get('reg_Memb. Suffix', '') or ''),
                str(crow.get('reg_Preferred Name', '') or ''),
            ]
            reg_words = get_name_words(' '.join(reg_name_fields))
            reg_gender = str(crow.get('reg_Gender', '') or '').upper()[:1]
            reg_bday = normalize_date(crow.get('reg_Birthday'))

            # Gender must match if both present
            if result_gender and reg_gender and result_gender != reg_gender:
                continue

            # Calculate score
            score = 0
            reasons = []

            # Name word matches (including fuzzy matches for spelling variants)
            exact_count, fuzzy_count, exact_words, fuzzy_words = count_matching_words(result_words, reg_words)
            total_word_matches = exact_count + fuzzy_count

            if total_word_matches >= 2:
                score += total_word_matches * 2
                match_details = []
                if exact_count > 0:
                    match_details.append(f'{exact_count} exact')
                if fuzzy_count > 0:
                    match_details.append(f'{fuzzy_count} fuzzy ({",".join(fuzzy_words)})')
                reasons.append(f'{total_word_matches} name words match ({", ".join(match_details)})')
            elif total_word_matches == 1 and len(result_words) <= 2:
                score += 1
                reasons.append('1 name word match (short name)')

            # Birthdate match (high confidence)
            if result_bday and reg_bday and result_bday == reg_bday:
                score += 5
                reasons.append('birthdate exact match')

            # Gender match bonus
            if result_gender and reg_gender and result_gender == reg_gender:
                score += 1
                reasons.append('gender match')

            if score > best_score:
                best_score = score
                best_match = crow
                best_reason = '; '.join(reasons)

        if best_match is not None and best_score >= 3:
            matches.append({
                'result_name': result_name,
                'result_bday': result_bday,
                'result_gender': result_gender,
                'result_club': result_club,
                'result_nation': result_nation,
                'reg_first': best_match.get('reg_Memb. First Name', ''),
                'reg_last': best_match.get('reg_Memb. Last Name', ''),
                'reg_middle': best_match.get('reg_Memb. Middle Initial', ''),
                'reg_suffix': best_match.get('reg_Memb. Suffix', ''),
                'reg_preferred': best_match.get('reg_Preferred Name', ''),
                'reg_bday': normalize_date(best_match.get('reg_Birthday')),
                'reg_gender': best_match.get('reg_Gender', ''),
                'reg_club': best_match.get('reg_CLUB_EXTRACTED', ''),
                'match_score': best_score,
                'match_reason': best_reason,
            })
        else:
            no_match.append({
                'result_name': result_name,
                'result_bday': result_bday,
                'result_gender': result_gender,
                'result_club': result_club,
                'result_nation': result_nation,
            })

    print(f'\n=== RESULTS ===')
    print(f'Potential matches found: {len(matches)}')
    print(f'No match found: {len(no_match)}')

    # Show sample matches
    print(f'\nTop 15 matches by score:')
    matches_sorted = sorted(matches, key=lambda x: x['match_score'], reverse=True)
    for m in matches_sorted[:15]:
        print(f"  {m['result_name']} ({m['result_bday']}) -> {m['reg_first']} {m['reg_last']} ({m['reg_bday']}) [score:{m['match_score']}] - {m['match_reason']}")

    # Save to Excel
    print(f'\nSaving to {OUTPUT_FILE}...')
    with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
        if matches:
            pd.DataFrame(matches_sorted).to_excel(writer, sheet_name='Potential Matches', index=False)
        if no_match:
            pd.DataFrame(no_match).to_excel(writer, sheet_name='No Match Found', index=False)

    print('Done!')

if __name__ == '__main__':
    main()
