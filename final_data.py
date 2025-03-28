import pandas as pd

# Load the CSV files
csv1 = pd.read_csv('static_websites_data.csv')
csv2 = pd.read_csv('dynamic_websites_data.csv')

# Combine the CSV files
combined_csv = pd.concat([csv1, csv2])

# Save the combined CSV to a new file
combined_csv.to_csv('final_result.csv', index=False)