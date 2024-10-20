# Filename: rule_api.py
from flask import Flask, request, jsonify
from ast_structure import Node, combine_rules, parse_rule_string  # Import functions from ast_structure.py
from mongodb import store_rule  # Import function to store the AST in MongoDB
import uuid  # To generate unique rule IDs

app = Flask(__name__)

# API endpoint to parse rule and create AST
@app.route('/createRule', methods=['POST'])
def create_rule():
    # Extract the rule string from the request body
    rule_string = request.json.get('rule_string')
    
    if not rule_string:
        return jsonify({"error": "No rule_string provided"}), 400

    try:
        # Generate the AST (Node object) using parse_rule_string from ast_structure.py
        ast = parse_rule_string(rule_string)
        
        # Generate a unique rule ID
        rule_id = f"rule_{uuid.uuid4().hex[:8]}"
        
        # Store the AST in MongoDB using store_rule from mongo_db_storage.py
        store_rule(ast.to_dict(), rule_id)
        
        # Return success message and rule ID
        return jsonify({
            "message": "Rule successfully parsed and stored",
            "rule_id": rule_id,
            "ast": ast.to_dict()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/combineRules', methods=['POST'])
def combine_rule():
    # Extract rules array from request body
    rules = request.json.get('rules')
    
    # Validate input
    if not rules:
        return jsonify({"error": "No rules provided"}), 400
    
    if not isinstance(rules, list):
        return jsonify({"error": "Rules must be provided as an array"}), 400
    
    if len(rules) < 2:
        return jsonify({"error": "At least two rules are required for combination"}), 400
    
    try:
        # Combine the rules using combine_rules function
        combined_ast = combine_rules(rules)
        
        if not combined_ast:
            return jsonify({"error": "Failed to combine rules"}), 500
        
        # Generate a new rule ID for the combined rule
        combined_rule_id = f"combined_rule_{uuid.uuid4().hex[:8]}"
        
        # Store the combined AST in MongoDB
        store_rule(combined_ast.to_dict(), combined_rule_id)
        
        # Return the combined AST and new rule ID
        return jsonify({
            "message": "Rules successfully combined and stored",
            "rule_id": combined_rule_id,
            "ast": combined_ast.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Error combining rules: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
