#[
#  [100, 120, 130],
#  [110, 140, null],
#  [120, null, null]
#]

import os
import requests
import numpy as np
from flask_cors import CORS
from dotenv import load_dotenv
from flask import Flask, request, jsonify   

load_dotenv()
app = Flask(__name__)
CORS(app)


@app.route('/triangle', methods=['POST'])
def calculate_triangle():
    try:
        # get JSON payload
        data = request.get_json()

        # Access and convert to NumPy
        triangle_list = data['data']
        triangle_array = np.array(triangle_list, dtype=np.float64)

        # sets return array
        arr  = np.empty(triangle_array.shape[1]-1)

        # go through the triangle array

        for y in range(triangle_array.shape[1]-1): #column index, skips last column because no ldf 
            
            i = 0
            temp = 0.0

            for x in range(triangle_array.shape[0]): # row index

                current = triangle_array[x, y]
                next = triangle_array[x, y+1]

                if np.isnan(next) or np.isnan(current):
                    continue
                else: 
                    ldf = next/current
                    temp += ldf
                    i += 1
            
            arr[y] = temp / i if i > 0 else 0  # avoid division by zero
        
        return jsonify({
            "message": "Triangle array processed successfully",
            "data": arr.tolist()  # convert NumPy array to list for JSON serialization
        }), 200 ## its fine to keep it like this for now.

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/ultimate_loss', methods=['POST'])
def calculate_ultimate_loss():
    try:
        # get JSON payload
        data = request.get_json()

        # Access and convert to NumPy
        ultimate_loss_year_data = data[0] # this is going to be data from the point in year and of what year is the triangle it is referring to so one float
        ultimate_loss_arr = data[1]
        result = []

        for x in range(len(ultimate_loss_arr)):
            ultimate_loss_year_data = ultimate_loss_year_data*ultimate_loss_arr[x]
            result.append(ultimate_loss_year_data)

        
        return jsonify({
            "message": "Ultimate loss array processed successfully",
            "data": result  # return the processed data
        }), 200
        


    except Exception as e:
        return jsonify({"error": str(e)}), 400
    

@app.route('/IBNR', methods=['POST'])
def IBNR():
    try: 
        data = request.get_json()
        cost_dealt = data[0]
        ultimate = data[1]
        IBNR = ultimate - cost_dealt

        return jsonify(
            {
                "message": "IBNR calculated successfully",
                "IBNR": IBNR  # return the calculated IBNR
            }
        ),200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/AI', methods=['POST'])
def AI():

    # AI response, empty check frontend

    try:
        # get JSON payload
        data = request.get_json()
        string = data['string']

        api_url = "https://openrouter.ai/api/v1/chat/completions"
        api_key = os.getenv('OPENROUTER_API_KEY')
        print(f"OPENROUTER_API_KEY loaded: {'YES' if api_key else 'NO'}")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek/deepseek-chat-v3-0324",  # or another supported model
            "messages": [
                {"role": "user", "content": string}
            ]
        }

        response = requests.post(api_url, headers=headers, json=payload)
        response_json = response.json()
        if response.status_code != 200:
            print(f"OpenRouter API error: {response_json}")
            return jsonify({"error": f"Failed to get response from AI service: {response_json}"}), response.status_code

        return jsonify({"content": response_json['choices'][0]['message']['content']}), 200
        


    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
@app.route('/bf_simulation', methods=['POST'])
def bf_simulation():
    try:
        # get JSON payload
        data = request.get_json()
        print('Received /bf_simulation payload:', data)
        ELR = data['ELR']
        RL = data['RL']
        LDF = data['LDF']
        EL = data.get('EL')
        Premium_Earned = data['Premium_Earned']

        if EL is None:
            EL = Premium_Earned * ELR

        BF = RL + (Premium_Earned * ELR * (1 - 1/LDF))

        return jsonify({
            "message": "Simulation processed successfully",
            "BF": BF,
            "formula": "BF = RL + (Premium_Earned * ELR * (1 - 1/LDF))",
            "inputs": {
                "RL": RL,
                "Premium_Earned": Premium_Earned,
                "ELR": ELR,
                "LDF": LDF,
                "EL": EL
            }
        }), 200
    except Exception as e:
        print('Error in /bf_simulation:', str(e))
        return jsonify({"error": str(e)}), 400


if __name__ == '__main__':
    app.run(debug=True)