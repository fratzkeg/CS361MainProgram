#!/usr/bin/env python3
from flask import Flask, request, jsonify
import uuid

app = Flask(__name__)

@app.route('/alerts', methods=['POST'])
def budget_alerts():
    correlation_id = request.headers.get('X-Correlation-ID', str(uuid.uuid4()))
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    required_fields = ['remainingBudget', 'warningThreshold', 'reserveBalance', 'reserveThreshold']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    try:
        rem_budget = float(data['remainingBudget'])
        warn_thresh = float(data['warningThreshold'])
        res_balance = float(data['reserveBalance'])
        res_thresh = float(data['reserveThreshold'])
    except (ValueError, TypeError):
        return jsonify({"error": "All budget and threshold fields must be numbers"}), 400

    alerts = []

    if rem_budget <= warn_thresh:
        alerts.append({
            "alert": "overspend",
            "message": "Remaining budget is within the warning threshold."
        })

    if res_balance < res_thresh:
        alerts.append({
            "alert": "low_reserve",
            "message": "Reserve balance is below the safe threshold."
        })

    return jsonify({
        "alerts": alerts,
        "correlationId": correlation_id
    })

if __name__ == '__main__':
    print("Starting Budget Alerts Microservice (port 5003)…")
    app.run(debug=True, host='0.0.0.0', port=5003)
