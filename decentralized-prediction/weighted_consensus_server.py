from flask import Flask, request, jsonify
import requests
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import json
from scipy.spatial.distance import euclidean

app = Flask(__name__)

MODEL_ENDPOINTS = [
    "http://localhost:5000/predict",
    "http://localhost:5001/predict",
    "http://localhost:5002/predict"
]

WEIGHTS_FILE = 'model_weights.json'

def load_weights():
    """Load model weights from JSON file"""
    try:
        with open(WEIGHTS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"weights": {endpoint: {"weight": 1.0} for endpoint in MODEL_ENDPOINTS}}

def save_weights(weights_data):
    """Save model weights to JSON file"""
    with open(WEIGHTS_FILE, 'w') as f:
        json.dump(weights_data, f, indent=4)

def update_weights(predictions, consensus_probability):
    """Update weights based on how close each prediction is to the consensus"""
    weights_data = load_weights()
    
    for pred, endpoint in zip(predictions, MODEL_ENDPOINTS):
        if pred is not None:
            distance = euclidean(pred['probability'], consensus_probability)
            
            new_weight = np.exp(-distance)
            
            old_weight = weights_data['weights'][endpoint]['weight']
            weights_data['weights'][endpoint]['weight'] = 0.7 * old_weight + 0.3 * new_weight
    
    save_weights(weights_data)
    return weights_data

def get_prediction(endpoint, params):
    """Get prediction from a single model"""
    try:
        response = requests.get(endpoint, params=params)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

@app.route('/weighted_predict', methods=['GET'])
def weighted_predict():
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
        valid_endpoints = [endpoint for p, endpoint in zip(predictions, MODEL_ENDPOINTS) if p is not None]
        
        if not valid_predictions:
            return jsonify({
                'status': 'error',
                'message': 'No valid predictions received'
            }), 400

        weights_data = load_weights()
        
        weights = [weights_data['weights'][endpoint]['weight'] for endpoint in valid_endpoints]
        weights = np.array(weights) / sum(weights)
        
        all_probabilities = [p['probability'] for p in valid_predictions]
        weighted_probability = np.average(all_probabilities, weights=weights, axis=0).tolist()
        
        weights_data = update_weights(valid_predictions, weighted_probability)
        
        consensus_prediction = int(np.argmax(weighted_probability))
        
        avg_accuracy = np.mean([p['model_accuracy'] for p in valid_predictions])
        
        return jsonify({
            'status': 'success',
            'consensus_prediction': consensus_prediction,
            'consensus_probability': weighted_probability,
            'iris_type': valid_predictions[0]['iris_type'],
            'average_model_accuracy': avg_accuracy,
            'number_of_models_responded': len(valid_predictions),
            'current_weights': weights.tolist(),
            'individual_predictions': valid_predictions
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004)