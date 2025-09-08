import streamlit as st
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

# Eksempeldata
data = {'x': [1, 2, 3, 4, 5], 'y': [10, 14, 12, 16, 18]}
df = pd.DataFrame(data)

st.header("Min Seaborn-graf i Streamlit")

# 1. Lag en figur og akse med Matplotlib
fig, ax = plt.subplots()

# 2. Bruk Seaborn til å plotte på den aksen
sns.lineplot(data=df, x='x', y='y', ax=ax)
ax.set_title("En enkel linjegraf")

# 3. Vis figuren i Streamlit
st.pyplot(fig)