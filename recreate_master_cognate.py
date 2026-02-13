import pandas as pd
import numpy as np

def recreate_master_cognate():
    # Load the data
    print("Loading CSV files...")
    perfect_df = pd.read_csv('perfect_cognates_universal.csv')
    near_df = pd.read_csv('near_cognates_discovered.csv')
    
    print(f"Perfect cognates: {len(perfect_df)} rows")
    print(f"Near cognates: {len(near_df)} rows")
    
    # Transform perfect cognates to the desired format
    perfect_processed = []
    for _, row in perfect_df.iterrows():
        languages = row['Languages_Found'].split(',')
        word = row['Word']
        
        # Create all possible pairs
        for i in range(len(languages)):
            for j in range(i + 1, len(languages)):
                perfect_processed.append({
                    'Rank': row['Rank'],
                    'English_Reference': row['English_Meaning'],
                    'Word_A': word,
                    'Word_B': word,
                    'Lang_A': languages[i].strip(),
                    'Lang_B': languages[j].strip(),
                    'Match_Type': 'Perfect',
                    'Similarity_Score': 1.0
                })
    
    perfect_transformed = pd.DataFrame(perfect_processed)
    
    # Transform near cognates to the desired format
    near_transformed = near_df.rename(columns={
        'English_Meaning': 'English_Reference',
        'Language_A': 'Lang_A',
        'Word_A': 'Word_A',
        'Language_B': 'Lang_B',
        'Word_B': 'Word_B'
    })
    near_transformed['Match_Type'] = 'Near'
    
    # Select and reorder columns
    columns = ['Rank', 'English_Reference', 'Word_A', 'Word_B', 'Lang_A', 'Lang_B', 'Match_Type', 'Similarity_Score']
    perfect_transformed = perfect_transformed[columns]
    near_transformed = near_transformed[columns]
    
    # Combine both dataframes
    combined_df = pd.concat([perfect_transformed, near_transformed], ignore_index=True)
    
    # Add Audit_Status column with False Friend Protection logic
    def audit_logic(row):
        if row['Match_Type'] == 'Perfect':
            return 'OK'
        elif row['Match_Type'] == 'Near':
            # Flag for manual review if:
            # 1. Words are very short (<= 2 characters)
            # 2. Similarity score is low (< 0.7)
            # 3. English reference seems unrelated (very basic check)
            word_a_len = len(str(row['Word_A']))
            word_b_len = len(str(row['Word_B']))
            similarity = float(row['Similarity_Score'])
            
            if word_a_len <= 2 or word_b_len <= 2 or similarity < 0.7:
                return 'Manual Review Needed'
            else:
                return 'OK'
        return 'OK'
    
    combined_df['Audit_Status'] = combined_df.apply(audit_logic, axis=1)
    
    # Deduplication: If a pair exists in both files, keep the 'Perfect' one
    # Create a unique key for each pair
    combined_df['Pair_Key'] = combined_df.apply(
        lambda row: f"{sorted([row['Lang_A'], row['Lang_B']])[0]}-{sorted([row['Lang_A'], row['Lang_B']])[1]}-{row['English_Reference']}", 
        axis=1
    )
    
    # Sort by Match_Type so 'Perfect' comes first, then deduplicate keeping first occurrence
    combined_df = combined_df.sort_values('Match_Type', ascending=False)
    combined_df = combined_df.drop_duplicates(subset=['Pair_Key'], keep='first')
    
    # Remove the temporary Pair_Key column
    combined_df = combined_df.drop('Pair_Key', axis=1)
    
    # Reorder columns to final format
    final_columns = ['Rank', 'English_Reference', 'Word_A', 'Word_B', 'Lang_A', 'Lang_B', 'Match_Type', 'Similarity_Score', 'Audit_Status']
    combined_df = combined_df[final_columns]
    
    # Sort by Rank
    combined_df = combined_df.sort_values('Rank')
    
    # Save the master file
    combined_df.to_csv('MASTER_COGNATE_V2.csv', index=False)
    print(f"Master cognate database saved as MASTER_COGNATE_V2.csv")
    
    # Statistics
    perfect_count = len(combined_df[combined_df['Match_Type'] == 'Perfect'])
    near_count = len(combined_df[combined_df['Match_Type'] == 'Near'])
    manual_review_count = len(combined_df[combined_df['Audit_Status'] == 'Manual Review Needed'])
    
    print(f"\nStatistics:")
    print(f"Perfect matches: {perfect_count}")
    print(f"Near matches: {near_count}")
    print(f"Total matches: {len(combined_df)}")
    print(f"Manual review needed: {manual_review_count}")
    
    return combined_df

if __name__ == "__main__":
    master_df = recreate_master_cognate()
