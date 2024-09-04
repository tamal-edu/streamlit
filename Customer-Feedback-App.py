import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report

# Load and preprocess data
@st.cache_data
def load_data():
    # Load your data here
    df = pd.read_csv('synthetic_it_service_provider_data.csv')
    # Preprocess data
    return df

df = load_data()

# Train sentiment analysis model
@st.cache_resource
def train_model(df):
    X = df['Customer Feedback']
    y = df['Sentiment']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    vectorizer = TfidfVectorizer()
    X_train_vectorized = vectorizer.fit_transform(X_train)
    X_test_vectorized = vectorizer.transform(X_test)
    
    model = RandomForestClassifier()
    model.fit(X_train_vectorized, y_train)
    
    return model, vectorizer

model, vectorizer = train_model(df)

# Streamlit app
st.title('Customer Feedback Analysis')

# Input for new feedback
new_feedback = st.text_area('Enter customer feedback:')
if new_feedback:
    # Predict sentiment
    new_feedback_vectorized = vectorizer.transform([new_feedback])
    sentiment = model.predict(new_feedback_vectorized)[0]
    st.write(f'Predicted Sentiment: {sentiment}')

# Data overview
st.subheader('Data Overview')
st.write(df.head())

# Visualizations
st.subheader('Customer Rating Distribution')
fig, ax = plt.subplots()
sns.countplot(x='Customer Rating (1-5)', data=df, ax=ax)
st.pyplot(fig)

st.subheader('Average Customer Rating by Service Type')
fig, ax = plt.subplots(figsize=(10, 6))
df.groupby('Service Type')['Customer Rating (1-5)'].mean().sort_values().plot(kind='bar', ax=ax)
plt.ylabel('Average Customer Rating')
plt.xticks(rotation=45)
st.pyplot(fig)
