import os
from flask import Flask, render_template, request, jsonify
from model import HousePriceModel

# Primary application instance
real_estate_app = Flask(__name__)

# Initialize the valuation engine
valuation_engine = HousePriceModel()

def bootstrap_model():
    """Confirms model availability or triggers training sequence"""
    if not valuation_engine.load_model():
        print("Model weights not found. Initializing training...")
        from model import train_and_save_model
        train_and_save_model()
        valuation_engine.load_model()

bootstrap_model()

# Validation constraints configuration
LIMITS = {
    'sq_ft': {'min': 500, 'max': 10000, 'label': 'Square footage'},
    'beds': {'min': 1, 'max': 10, 'label': 'Bedrooms'},
    'baths': {'min': 1, 'max': 8, 'label': 'Bathrooms'},
    'age': {'min': 0, 'max': 100, 'label': 'Property age'},
    'parking': {'min': 0, 'max': 4, 'label': 'Garage capacity'},
    'area_rank': {'min': 1, 'max': 10, 'label': 'Neighborhood score'}
}

@real_estate_app.route('/')
def index():
    """Serves the property valuation interface"""
    return render_template('index.html')

@real_estate_app.route('/estimate-price', methods=['POST'])
def calculate_valuation():
    """Processes property details and returns market estimate"""
    try:
        incoming_data = request.get_json()
        
        # Clean and map variables
        params = {
            'square_feet': float(incoming_data.get('square_feet', 0)),
            'bedrooms': int(incoming_data.get('bedrooms', 0)),
            'bathrooms': float(incoming_data.get('bathrooms', 0)),
            'age_years': int(incoming_data.get('age_years', 0)),
            'garage_spaces': int(incoming_data.get('garage_spaces', 0)),
            'location_score': int(incoming_data.get('location_score', 0))
        }

        # Dynamic validation logic
        valid_map = {
            'sq_ft': params['square_feet'],
            'beds': params['bedrooms'],
            'baths': params['bathrooms'],
            'age': params['age_years'],
            'parking': params['garage_spaces'],
            'area_rank': params['location_score']
        }

        for key, value in valid_map.items():
            rule = LIMITS[key]
            if value < rule['min'] or value > rule['max']:
                return jsonify({
                    'status': 'error',
                    'message': f"{rule['label']} must be between {rule['min']} and {rule['max']}"
                }), 400

        # Generate result from engine
        market_estimate = valuation_engine.predict(**params)

        return jsonify({
            'status': 'success',
            'data': {
                'valuation': round(market_estimate, 2),
                'currency': 'USD',
                'parameters_processed': params
            }
        })

    except Exception as failure:
        return jsonify({
            'status': 'fail',
            'message': str(failure)
        }), 500

if __name__ == '__main__':
    # Execute development server
    real_estate_app.run(
        host='0.0.0.0', 
        port=8080, 
        debug=False
    )