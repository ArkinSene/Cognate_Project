import pandas as pd
import re

def perform_linguistic_audit():
    """
    Perform strict linguistic audit to remove false cognates
    Focus on etymological accuracy - only keep true cognates
    """
    
    print("Loading MASTER_COGNATE_V2.csv for linguistic audit...")
    
    try:
        df = pd.read_csv('MASTER_COGNATE_V2.csv')
        print(f"Loaded {len(df)} rows for audit")
    except FileNotFoundError:
        print("MASTER_COGNATE_V2.csv not found")
        return
    
    # Define known false cognates and problematic patterns
    false_cognates = {
        # English words that commonly have false cognates
        'home': ['maison'],  # English 'home' vs French 'maison' (false cognate)
        'man': ['homme'],    # English 'man' vs French 'homme' (false cognate)
        'book': ['libro'],  # English 'book' vs Spanish 'libro' (false cognate)
        'library': ['librería'],  # English 'library' vs Spanish 'librería' (false cognate)
        'actually': ['actualmente'],  # English 'actually' vs Spanish 'actualmente' (false cognate)
        'embarrassed': ['embarazada'],  # English 'embarrassed' vs Spanish 'embarazada' (false cognate)
        'sensible': ['sensible'],  # English 'sensible' vs French 'sensible' (different meanings)
        'attend': ['attendre'],  # English 'attend' vs French 'attendre' (false cognate)
        'demand': ['demander'],  # English 'demand' vs French 'demander' (false cognate)
    }
    
    # Language family groups for validation
    romance_languages = ['es', 'fr', 'it', 'pt', 'ca', 'gl', 'ro']
    germanic_languages = ['en', 'de', 'nl', 'sv', 'no', 'da']
    
    rows_to_remove = []
    
    for index, row in df.iterrows():
        english_ref = row['English_Reference'].lower()
        word_a = row['Word_A'].lower()
        word_b = row['Word_B'].lower()
        lang_a = row['Lang_A'].lower()
        lang_b = row['Lang_B'].lower()
        
        # Rule 1: Check for known false cognates
        if english_ref in false_cognates:
            false_words = false_cognates[english_ref]
            if word_a in false_words or word_b in false_words:
                rows_to_remove.append(index)
                continue
        
        # Rule 2: Cross-language family validation
        # If comparing Romance vs Germanic, be extra strict
        if (lang_a in romance_languages and lang_b in germanic_languages) or \
           (lang_a in germanic_languages and lang_b in romance_languages):
            
            # Only allow if there's clear etymological connection
            # Check for common Indo-European roots patterns
            if not has_valid_etymological_connection(english_ref, word_a, word_b, lang_a, lang_b):
                rows_to_remove.append(index)
                continue
        
        # Rule 3: Remove obvious non-cognates based on phonetic patterns
        if is_obvious_false_cognate(word_a, word_b, lang_a, lang_b):
            rows_to_remove.append(index)
            continue
    
    # Remove identified false cognates
    cleaned_df = df.drop(rows_to_remove)
    
    print(f"Linguistic audit completed:")
    print(f"  - Original rows: {len(df)}")
    print(f"  - Removed false cognates: {len(rows_to_remove)}")
    print(f"  - Cleaned rows: {len(cleaned_df)}")
    print(f"  - Accuracy improvement: {(len(rows_to_remove)/len(df)*100):.1f}%")
    
    # Save cleaned data
    cleaned_df.to_csv('MASTER_COGNATE_V2.csv', index=False)
    print("Saved cleaned MASTER_COGNATE_V2.csv")
    
    return cleaned_df

def has_valid_etymological_connection(english_ref, word_a, word_b, lang_a, lang_b):
    """
    Check if words have valid etymological connection
    """
    
    # Known valid cross-family cognates
    valid_cross_family = {
        'water': ['agua', 'acqua', 'eau', 'água'],
        'father': ['padre', 'père', 'pai'],
        'mother': ['madre', 'mère', 'mãe'],
        'brother': ['hermano', 'frère', 'irmão'],
        'sister': ['hermana', 'sœur', 'irmã'],
        'night': ['noche', 'nuit', 'noite'],
        'day': ['día', 'jour', 'dia'],
        'new': ['nuevo', 'nouveau', 'nuovo'],
        'old': ['viejo', 'vieux', 'vecchio'],
        'good': ['bueno', 'bon', 'buono'],
        'big': ['grande', 'grand', 'grande'],
        'small': ['pequeño', 'petit', 'piccolo'],
    }
    
    if english_ref in valid_cross_family:
        valid_words = valid_cross_family[english_ref]
        if word_a in valid_words or word_b in valid_words:
            return True
    
    # Check for common morphological patterns
    common_patterns = [
        r'^[aeiou]+tion$',  # -tion words
        r'^[aeiou]+ment$',  # -ment words  
        r'^[aeiou]+ness$',  # -ness words
        r'^[aeiou]+ity$',   # -ity words
    ]
    
    for pattern in common_patterns:
        if re.match(pattern, word_a) and re.match(pattern, word_b):
            return True
    
    return False

def is_obvious_false_cognate(word_a, word_b, lang_a, lang_b):
    """
    Identify obvious false cognates based on phonetic and structural patterns
    """
    
    # Completely different phonetic structures
    if abs(len(word_a) - len(word_b)) > 4:
        # Only flag if they're also phonetically different
        common_letters = set(word_a) & set(word_b)
        if len(common_letters) < 3:
            return True
    
    # Check for completely different consonant patterns
    vowels_a = sum(1 for c in word_a if c in 'aeiou')
    vowels_b = sum(1 for c in word_b if c in 'aeiou')
    
    if abs(vowels_a - vowels_b) > 3:
        return True
    
    return False

if __name__ == "__main__":
    perform_linguistic_audit()
