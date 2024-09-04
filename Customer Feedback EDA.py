import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import StringIO

# # Assuming the data is in a string variable called 'data_string'
# data = StringIO('''Request ID	Customer ID	Customer Name	Customer Company	Request Date	Service Type	Capability	Issue Description	Assigned Team	Resolution Time (hours)	Status	Customer Feedback	Customer Rating (1-5)	Escalation (Yes/No)	Complaint	Compliment	General Comment	Expectation	Sentiment
# c6406163-5b3d-4b4d-ae6f-cdfd49d8ac26	8acdc93c-3376-4f39-8828-8002e9b7166a	Michael Young	Miller-Flores	05/03/2024	On-site Support	Cloud Services	Daughter second story class involve out might near.	Team D	13.37	Resolved	Once so leave could.	1	No	Age participant visit west claim article.	War or event company.		Focus garden dog fire send stay.	Neutral
# ...''')  # Add the rest of the data here

# Read the data
#df = pd.read_csv(data, sep='\t')
df = pd.read_csv('synthetic_it_service_provider_data.csv')


# Display basic information about the dataset
print(df.info())

# Display the first few rows
print(df.head())

# Check for missing values
print(df.isnull().sum())

# Display summary statistics
print(df.describe())

# Display unique values in categorical columns
categorical_columns = ['Service Type', 'Capability', 'Assigned Team', 'Status', 'Escalation (Yes/No)', 'Sentiment']
for col in categorical_columns:
    print(f"\nUnique values in {col}:")
    print(df[col].value_counts())

# Visualize the distribution of Customer Ratings
plt.figure(figsize=(10, 6))
sns.countplot(x='Customer Rating (1-5)', data=df)
plt.title('Distribution of Customer Ratings')
plt.show()

# Visualize the relationship between Resolution Time and Customer Rating
plt.figure(figsize=(10, 6))
sns.scatterplot(x='Resolution Time (hours)', y='Customer Rating (1-5)', data=df)
plt.title('Resolution Time vs Customer Rating')
plt.show()

# Visualize the average Customer Rating by Service Type
plt.figure(figsize=(12, 6))
df.groupby('Service Type')['Customer Rating (1-5)'].mean().sort_values().plot(kind='bar')
plt.title('Average Customer Rating by Service Type')
plt.ylabel('Average Customer Rating')
plt.xticks(rotation=45)
plt.show()

# Visualize the distribution of Sentiments
plt.figure(figsize=(10, 6))
sns.countplot(x='Sentiment', data=df)
plt.title('Distribution of Sentiments')
plt.show()