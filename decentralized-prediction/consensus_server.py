from flask import Flask, request, jsonify
import requests
import numpy as np
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

MODEL_ENDPOINTS = [
    "http://localhost:5000/predict",
    "http://localhost:5001/predict",
    "http://localhost:5002/predict"
]

def get_prediction(endpoint, params):
    """Get prediction from a single model"""
    try:
        response = requests.get(endpoint, params=params)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

@app.route('/consensus_predict', methods=['GET'])
def consensus_predict():
    try:
        params = {
            'sepal_length': request.args.get('sepal_length'),
            'sepal_width': request.args.get('sepal_width'),
            'petal_length': request.args.get('petal_length'),
            'petal_width': request.args.get('petal_width')
        }
        
        with ThreadPoolExecutor(max_workers=len(MODEL_ENDPOINTS)) as executor:
            predictions = list(executor.map(
                lambda endpoint: get_prediction(endpoint, params),
                MODEL_ENDPOINTS
            ))
        
        valid_predictions = [p for p in predictions if p is not None]
        
        if not valid_predictions:
            return jsonify({
                'status': 'error',
                'message': 'No valid predictions received'
            }), 400

        all_probabilities = [p['probability'] for p in valid_predictions]
        consensus_probability = np.mean(all_probabilities, axis=0).tolist()
        
        consensus_prediction = int(np.argmax(consensus_probability))
        
        avg_accuracy = np.mean([p['model_accuracy'] for p in valid_predictions])
        
        iris_type = valid_predictions[0]['iris_type']
        
        return jsonify({
            'status': 'success',
            'consensus_prediction': consensus_prediction,
            'consensus_probability': consensus_probability,
            'iris_type': iris_type,
            'average_model_accuracy': avg_accuracy,
            'number_of_models_responded': len(valid_predictions),
            'individual_predictions': valid_predictions
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)