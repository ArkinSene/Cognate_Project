import pandas as pd
import os

def merge_datasets():
    print("Starting merge...")
    
    # Check if files exist
    if not os.path.exists("perfect_cognates_universal.csv") or not os.path.exists("near_cognates_discovered.csv"):
        print("Error: One or both source CSV files are missing!")
        return

    # Load data
    perfect_df = pd.read_csv("perfect_cognates_universal.csv")
    near_df = pd.read_csv("near_cognates_discovered.csv")

    # 1. Standardize Perfect Cognates
    # We turn the 'Languages_Found' column into Word_A/Word_B format to match
    perfect_df['Match_Type'] = 'Perfect'
    perfect_df = perfect_df.rename(columns={
        'English_Meaning': 'English_Reference',
        'Word': 'Word_A',
        'Languages_Found': 'Languages'
    })
    # For perfect matches, A and B are the same
    perfect_df['Word_B'] = perfect_df['Word_A']
    perfect_df['Details'] = "Identical Spelling"

    # 2. Standardize Near Cognates
    near_df['Match_Type'] = 'Near'
    # Create a 'Languages' column for consistency
    near_df['Languages'] = near_df['Lang_A'] + ", " + near_df['Lang_B']
    near_df = near_df.rename(columns={'Score': 'Details'})

    # 3. Combine
    cols = ['Rank', 'English_Reference', 'Match_Type', 'Word_A', 'Word_B', 'Languages', 'Details']
    master_list = pd.concat([perfect_df[cols], near_df[cols]], ignore_index=True)

    # 4. Final Polish
    master_list = master_list.sort_values(by='Rank')
    
    # Save
    master_list.to_csv("MASTER_COGNATE_LIST.csv", index=False)
    print(f"Success! Created MASTER_COGNATE_LIST.csv with {len(master_list)} rows.")

if __name__ == "__main__":
    merge_datasets()