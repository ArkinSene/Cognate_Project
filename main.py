import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import random
from typing import List, Optional
from pydantic import BaseModel

app = FastAPI(title="Cognate Database API", description="API for searching and exploring cognates")

class LanguageRequest(BaseModel):
    languages: List[str]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for GitHub Pages frontend
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# Load master cognate database with memory optimization for production
try:
    # Use low_memory=False and dtype optimization for better performance
    cognates_df = pd.read_csv(
        'MASTER_COGNATE_V2.csv',
        low_memory=False,
        dtype={
            'Rank': 'int32',
            'English_Reference': 'string',
            'Word_A': 'string',
            'Word_B': 'string',
            'Lang_A': 'string',
            'Lang_B': 'string',
            'Match_Type': 'string',
            'Similarity_Score': 'float32',
            'Audit_Status': 'string'
        }
    )
    print(f"Loaded {len(cognates_df)} cognates from MASTER_COGNATE_V2.csv")
except FileNotFoundError:
    print("Warning: MASTER_COGNATE_V2.csv not found. Please run the recreate script first.")
    cognates_df = pd.DataFrame()

@app.get("/")
async def root():
    return {"message": "Cognate Database API", "total_cognates": len(cognates_df)}

@app.get("/search")
async def search_cognates(q: str):
    """
    Language Global Search: Find all cognates that share the same English_Reference
    Searches in English_Reference, Word_A, and Word_B columns
    """
    if cognates_df.empty:
        raise HTTPException(status_code=503, detail="Cognate database not loaded")
    
    query = q.lower().strip()
    
    # Search in English_Reference, Word_A, and Word_B columns
    mask_english = cognates_df['English_Reference'].str.lower().str.contains(query, na=False)
    mask_a = cognates_df['Word_A'].str.lower().str.contains(query, na=False)
    mask_b = cognates_df['Word_B'].str.lower().str.contains(query, na=False)
    
    # Find initial matches
    initial_matches = cognates_df[mask_english | mask_a | mask_b]
    
    if initial_matches.empty:
        return {"message": f"No cognates found for '{q}'", "results": []}
    
    # Get unique English_Reference values from initial matches
    english_references = initial_matches['English_Reference'].unique().tolist()
    
    # Collect ALL cognates that share these English_Reference values
    global_matches = cognates_df[cognates_df['English_Reference'].isin(english_references)]
    
    # Group by English_Reference for organized response
    grouped_results = {}
    for english_ref in english_references:
        ref_data = global_matches[global_matches['English_Reference'] == english_ref]
        
        # Collect all unique translations for this English word
        translations = {}
        for _, row in ref_data.iterrows():
            # Add language A and its word
            lang_a = row['Lang_A']
            word_a = row['Word_A']
            if lang_a not in translations:
                translations[lang_a] = []
            if word_a not in translations[lang_a]:
                translations[lang_a].append(word_a)
            
            # Add language B and its word
            lang_b = row['Lang_B']
            word_b = row['Word_B']
            if lang_b not in translations:
                translations[lang_b] = []
            if word_b not in translations[lang_b]:
                translations[lang_b].append(word_b)
        
        # Sort languages and remove duplicates within each language
        sorted_translations = {}
        for lang in sorted(translations.keys()):
            sorted_translations[lang] = sorted(list(set(translations[lang])))
        
        grouped_results[english_ref] = {
            "english_word": english_ref,
            "translations": sorted_translations,
            "language_count": len(sorted_translations),
            "total_translations": sum(len(words) for words in sorted_translations.values()),
            "match_types": ref_data['Match_Type'].unique().tolist()
        }
    
    return {
        "query": q,
        "english_references_found": len(english_references),
        "total_cognate_pairs": len(global_matches),
        "results": grouped_results
    }

@app.get("/language/{code}")
async def get_by_language(code: str, match_type: Optional[str] = None):
    """
    Get cognates filtered by language code
    Optional match_type filter: 'Perfect' or 'Near'
    """
    if cognates_df.empty:
        raise HTTPException(status_code=503, detail="Cognate database not loaded")
    
    lang_code = code.lower().strip()
    
    # Filter by language in either Lang_A or Lang_B
    mask = (cognates_df['Lang_A'].str.lower() == lang_code) | (cognates_df['Lang_B'].str.lower() == lang_code)
    results = cognates_df[mask]
    
    # Optional match type filter
    if match_type:
        match_type = match_type.capitalize()
        if match_type in ['Perfect', 'Near']:
            results = results[results['Match_Type'] == match_type]
        else:
            raise HTTPException(status_code=400, detail="match_type must be 'Perfect' or 'Near'")
    
    if results.empty:
        return {"message": f"No cognates found for language '{code}'", "results": []}
    
    return {
        "language": code,
        "count": len(results),
        "results": results.to_dict('records')
    }

@app.get("/random")
async def get_random_cognates(count: int = 5):
    """
    Get random English_Reference groups with all their cognates
    """
    if cognates_df.empty:
        raise HTTPException(status_code=503, detail="Cognate database not loaded")
    
    if count <= 0 or count > 100:
        raise HTTPException(status_code=400, detail="Count must be between 1 and 100")
    
    # Get unique English_Reference values
    unique_english_refs = cognates_df['English_Reference'].unique().tolist()
    
    # Pick random English_Reference groups
    if len(unique_english_refs) < count:
        selected_refs = unique_english_refs
    else:
        selected_refs = random.sample(unique_english_refs, count)
    
    # Get all cognates for the selected English references
    random_results = cognates_df[cognates_df['English_Reference'].isin(selected_refs)]
    
    return {
        "count": len(selected_refs),
        "total_cognate_pairs": len(random_results),
        "results": random_results.to_dict('records')
    }

@app.post("/matrix")
async def create_comparative_matrix(request: LanguageRequest):
    """
    Create a comparative matrix of cognates across specified languages
    Returns data optimized for frontend table display
    """
    if cognates_df.empty:
        raise HTTPException(status_code=503, detail="Cognate database not loaded")
    
    if not request.languages:
        raise HTTPException(status_code=400, detail="Languages list cannot be empty")
    
    # Normalize language codes
    requested_languages = [lang.lower().strip() for lang in request.languages]
    
    # Filter data for requested languages
    filtered_df = cognates_df[
        (cognates_df['Lang_A'].str.lower().isin(requested_languages)) |
        (cognates_df['Lang_B'].str.lower().isin(requested_languages))
    ].copy()
    
    if filtered_df.empty:
        return {
            "languages": requested_languages,
            "total_words": 0,
            "matrix": []
        }
    
    # Create matrix data structure
    matrix_data = []
    
    # Group by English_Reference
    grouped = filtered_df.groupby('English_Reference')
    
    for english_ref, group in grouped:
        row = {"english_word": english_ref}
        
        # Initialize all language columns with empty strings
        for lang in requested_languages:
            row[lang] = ""
        
        # Fill in cognates for each language
        for _, cognate_row in group.iterrows():
            lang_a = cognate_row['Lang_A'].lower()
            lang_b = cognate_row['Lang_B'].lower()
            word_a = cognate_row['Word_A']
            word_b = cognate_row['Word_B']
            
            # Add word for language A if it's in our requested languages
            if lang_a in requested_languages:
                if not row[lang_a]:  # Only fill if empty
                    row[lang_a] = word_a
                elif word_a not in row[lang_a].split(', '):
                    row[lang_a] += ', ' + word_a
            
            # Add word for language B if it's in our requested languages
            if lang_b in requested_languages:
                if not row[lang_b]:  # Only fill if empty
                    row[lang_b] = word_b
                elif word_b not in row[lang_b].split(', '):
                    row[lang_b] += ', ' + word_b
        
        matrix_data.append(row)
    
    # Sort by English word
    matrix_data.sort(key=lambda x: x["english_word"])
    
    return {
        "languages": requested_languages,
        "total_words": len(matrix_data),
        "matrix": matrix_data
    }

@app.get("/stats")
async def get_statistics():
    """
    Get statistics about the cognate database
    """
    if cognates_df.empty:
        raise HTTPException(status_code=503, detail="Cognate database not loaded")
    
    perfect_count = len(cognates_df[cognates_df['Match_Type'] == 'Perfect'])
    near_count = len(cognates_df[cognates_df['Match_Type'] == 'Near'])
    manual_review_count = len(cognates_df[cognates_df['Audit_Status'] == 'Manual Review Needed'])
    
    # Get unique languages
    languages_a = cognates_df['Lang_A'].unique().tolist()
    languages_b = cognates_df['Lang_B'].unique().tolist()
    all_languages = sorted(list(set(languages_a + languages_b)))
    
    return {
        "total_cognates": len(cognates_df),
        "perfect_matches": perfect_count,
        "near_matches": near_count,
        "manual_review_needed": manual_review_count,
        "unique_languages": all_languages,
        "language_count": len(all_languages)
    }

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "database_loaded": not cognates_df.empty,
        "total_records": len(cognates_df)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
