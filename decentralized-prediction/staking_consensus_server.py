from flask import Flask, request, jsonify
import requests
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import json
from scipy.spatial.distance import euclidean
from datetime import datetime

app = Flask(__name__)

MODEL_ENDPOINTS = [
    "http://localhost:5000/predict",
    "http://localhost:5001/predict",
    "http://localhost:5002/predict",
    "http://localhost:5006/predict"
]

STAKES_FILE = 'model_stakes.json'
SLASH_THRESHOLD = 0.05
SLASH_AMOUNT = 200

def load_stakes():
    try:
        with open(STAKES_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "models": {
                endpoint: {
                    "weight": 1.0,
                    "stake": 1000.0,
                    "total_predictions": 0,
                    "successful_predictions": 0
                } for endpoint in MODEL_ENDPOINTS
            },
            "history": []
        }

def save_stakes(stakes_data):
    with open(STAKES_FILE, 'w') as f:
        json.dump(stakes_data, f, indent=4)

def slash_stake(stakes_data, endpoint, amount, reason):
    model_data = stakes_data["models"][endpoint]
    model_data["stake"] = max(0, model_data["stake"] - amount)
    
    stakes_data["history"].append({
        "timestamp": datetime.now().isoformat(),
        "model": endpoint,
        "action": "slash",
        "amount": amount,
        "reason": reason,
        "remaining_stake": model_data["stake"]
    })

def update_stakes_and_weights(predictions, valid_endpoints, consensus_probability, stakes_data):
    for pred, endpoint in zip(predictions, valid_endpoints):
        if pred is not None:
            model_data = stakes_data["models"][endpoint]
            distance = euclidean(pred['probability'], consensus_probability)
            model_data["total_predictions"] += 1
            
            if distance <= SLASH_THRESHOLD:
                model_data["successful_predictions"] += 1
            else:
                slash_stake(stakes_data, endpoint, SLASH_AMOUNT, 
                          f"Distance from consensus: {distance:.3f}")
            
            accuracy_rate = model_data["successful_predictions"] / model_data["total_predictions"]
            model_data["weight"] = (model_data["stake"] / 1000.0) * accuracy_rate
    
    save_stakes(stakes_data)
    return stakes_data

def get_prediction(endpoint, params):
    try:
        response = requests.get(endpoint, params=params)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

@app.route('/stake_predict', methods=['GET'])
def stake_predict():
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

        stakes_data = load_stakes()
        weights = [stakes_data["models"][endpoint]["weight"] for endpoint in valid_endpoints]
        weights = np.array(weights) / sum(weights)
        
        all_probabilities = [p['probability'] for p in valid_predictions]
        weighted_probability = np.average(all_probabilities, weights=weights, axis=0).tolist()
        
        stakes_data = update_stakes_and_weights(
            valid_predictions, 
            valid_endpoints,
            weighted_probability,
            stakes_data
        )
        
        consensus_prediction = int(np.argmax(weighted_probability))
        
        model_statuses = [{
            'endpoint': endpoint,
            'stake': stakes_data["models"][endpoint]["stake"],
            'weight': stakes_data["models"][endpoint]["weight"],
            'successful_predictions': stakes_data["models"][endpoint]["successful_predictions"],
            'total_predictions': stakes_data["models"][endpoint]["total_predictions"]
        } for endpoint in valid_endpoints]
        
        return jsonify({
            'status': 'success',
            'consensus_prediction': consensus_prediction,
            'consensus_probability': weighted_probability,
            'iris_type': valid_predictions[0]['iris_type'],
            'number_of_models_responded': len(valid_predictions),
            'model_statuses': model_statuses,
            'individual_predictions': valid_predictions
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@app.route('/stakes', methods=['GET'])
def get_stakes():
    stakes_data = load_stakes()
    return jsonify(stakes_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005)