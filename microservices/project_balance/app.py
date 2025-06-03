#!/usr/bin/env python3
from flask import Flask, request, jsonify
from datetime import datetime, date, timedelta
import uuid

app = Flask(__name__)

@app.route('/project-balance', methods=['POST'])
def project_balance():
    correlation_id = request.headers.get('X-Correlation-ID', str(uuid.uuid4()))
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    required_fields = ['currentBalance', 'dailyLimit', 'projectionEndDate']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    try:
        current_balance = float(data['currentBalance'])
        daily_limit = float(data['dailyLimit'])
    except (ValueError, TypeError):
        return jsonify({"error": "'currentBalance' and 'dailyLimit' must be numbers"}), 400

    try:
        proj_end = datetime.strptime(data['projectionEndDate'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"error": "projectionEndDate must be 'YYYY-MM-DD'"}), 400

    today = date.today()
    results = []
    day = today + timedelta(days=1)

    while day <= proj_end:
        current_balance -= daily_limit
        results.append({
            "date": day.isoformat(),
            "projectedBalance": round(current_balance, 2)
        })
        day += timedelta(days=1)

    response = {
        "projection": results,
        "correlationId": correlation_id
    }
    return jsonify(response)

if __name__ == '__main__':
    print("Starting Future Balance Projection Microservice (port 5002)…")
    app.run(debug=True, host='0.0.0.0', port=5002)
