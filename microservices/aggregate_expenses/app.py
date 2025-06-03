#!/usr/bin/env python3
from flask import Flask, request, jsonify
import uuid

app = Flask(__name__)

@app.route('/aggregate-expenses', methods=['POST'])
def aggregate_expenses():
    correlation_id = request.headers.get('X-Correlation-ID', str(uuid.uuid4()))
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    if 'expenses' not in data:
        return jsonify({"error": "Missing required field: expenses"}), 400

    try:
        expenses_list = data['expenses']
        totals = {}
        for exp in expenses_list:
            cat = exp.get('category')
            amt = exp.get('amount')
            if cat is None or amt is None:
                return jsonify({"error": "Each expense must have 'category' and 'amount'"}), 400
            if not isinstance(amt, (int, float)):
                return jsonify({"error": "'amount' must be a number"}), 400

            totals[cat] = totals.get(cat, 0.0) + amt

        # Omit zero or negative totals
        result = {cat: round(total, 2) for cat, total in totals.items() if total > 0}
    except Exception as e:
        return jsonify({"error": f"Failed to aggregate: {str(e)}"}), 500

    result['correlationId'] = correlation_id
    return jsonify(result)

if __name__ == '__main__':
    print("Starting Expense Aggregation Microservice (port 5001)…")
    app.run(debug=True, host='0.0.0.0', port=5001)
