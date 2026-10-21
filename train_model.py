
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np

# Load dataset
df = pd.read_csv("Nassau Candy Distributor.csv")

# Select features and target
data = df[
    ["Product Name", "Region", "Ship Mode", "Units", "Gross Profit"]
].copy()

data["Units"] = pd.to_numeric(data["Units"], errors="coerce")
data["Gross Profit"] = pd.to_numeric(
    data["Gross Profit"], errors="coerce"
)
data = data.dropna()

X = data[["Product Name", "Region", "Ship Mode", "Units"]]
y = data["Gross Profit"]

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Prepare text and numerical features
preprocessor = ColumnTransformer([
    (
        "cat",
        OneHotEncoder(handle_unknown="ignore"),
        ["Product Name", "Region", "Ship Mode"]
    ),
    ("num", "passthrough", ["Units"])
])

# Train model
model = Pipeline([
    ("preprocessor", preprocessor),
    ("model", GradientBoostingRegressor(random_state=42))
])

model.fit(X_train, y_train)

# Evaluate model
predictions = model.predict(X_test)

print("Model trained successfully!")
print("Training rows:", len(X_train))
print("Testing rows:", len(X_test))
print("MAE:", round(mean_absolute_error(y_test, predictions), 3))
print(
    "RMSE:",
    round(np.sqrt(mean_squared_error(y_test, predictions)), 3)
)
print("R2 Score:", round(r2_score(y_test, predictions), 3))

# Save model in the local environment
joblib.dump(model, "gross_profit_model.pkl")

print("\nModel saved as gross_profit_model.pkl")
