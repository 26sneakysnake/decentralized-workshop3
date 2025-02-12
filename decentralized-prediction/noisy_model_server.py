from flask import Flask, request, jsonify
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import numpy as np

app = Flask(__name__)

iris = load_iris()
X = iris.data
y = iris.target

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

accuracy = model.score(X_test, y_test)

@app.route('/predict', methods=['GET'])
def predict():
    try:
        sepal_length = float(request.args.get('sepal_length'))
        sepal_width = float(request.args.get('sepal_width'))
        petal_length = float(request.args.get('petal_length'))
        petal_width = float(request.args.get('petal_width'))
        
        features = np.array([[sepal_length, sepal_width, petal_length, petal_width]])
        prediction = model.predict(features)[0]
        probability = model.predict_proba(features)[0]
        
        noise = np.random.normal(0, 0.2, 3)
        noisy_probability = probability + noise
        noisy_probability = np.clip(noisy_probability, 0, 1)
        noisy_probability = noisy_probability / noisy_probability.sum()
        
        return jsonify({
            'status': 'success',
            'prediction': int(prediction),
            'probability': noisy_probability.tolist(),
            'iris_type': iris.target_names[prediction],
            'model_accuracy': accuracy,
            'model_type': 'NoisyRandomForest'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5006)