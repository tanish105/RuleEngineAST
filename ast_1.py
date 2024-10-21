from flask import Flask, request, jsonify

app = Flask(__name__)

class Node:
    def __init__(self, node_type, value=None, left=None, right=None):
        self.node_type = node_type
        self.value = value
        self.left = left
        self.right = right

    @classmethod
    def from_dict(cls, data):
        if data is None:
            return None
        return cls(
            node_type=data['node_type'],
            value=data['value'],
            left=cls.from_dict(data['left']) if data.get('left') else None,
            right=cls.from_dict(data['right']) if data.get('right') else None
        )

def evaluate_rule_logic(ast, data):
    def evaluate_node(node):
        if node.node_type == "operator":
            left_result = evaluate_node(node.left)
            right_result = evaluate_node(node.right)
            
            if node.value == "AND":
                return left_result and right_result
            elif node.value == "OR":
                return left_result or right_result
            
        elif node.node_type == "operand":
            # Parse the operand value into field, operator, and comparison value
            parts = node.value.split()
            field = parts[0]
            operator = parts[1]
            # Handle string values with quotes
            if len(parts) > 3:  # Case for strings with spaces
                comparison_value = ' '.join(parts[2:]).strip("'\"")
            else:
                comparison_value = parts[2].strip("'\"")
            
            # Get the actual value from data
            if field not in data:
                return False
            
            actual_value = data[field]
            
            # Convert comparison value to appropriate type based on actual value
            if isinstance(actual_value, (int, float)):
                try:
                    comparison_value = float(comparison_value)
                except ValueError:
                    return False
            
            # Perform the comparison
            if operator == '>':
                return actual_value > comparison_value
            elif operator == '<':
                return actual_value < comparison_value
            elif operator == '>=':
                return actual_value >= comparison_value
            elif operator == '<=':
                return actual_value <= comparison_value
            elif operator == '=':
                return actual_value == comparison_value
            elif operator == '!=':
                return actual_value != comparison_value
            else:
                raise ValueError(f"Unsupported operator: {operator}")
        
        return False

    return evaluate_node(ast)

@app.route('/evaluateRule', methods=['POST'])
def evaluate_rule_endpoint():
    # Extract rule AST and data from request body
    request_data = request.get_json()
    
    if not request_data:
        return jsonify({"error": "No data provided"}), 400
    
    ast_dict = request_data.get('rule')
    data = request_data.get('data')
    
    # Validate input
    if not ast_dict:
        return jsonify({"error": "Rule AST must be provided"}), 400
    
    if not data:
        return jsonify({"error": "Data must be provided"}), 400
    
    if not isinstance(data, dict):
        return jsonify({"error": "Data must be a dictionary"}), 400
    
    try:
        # Convert dictionary to Node object
        ast = Node.from_dict(ast_dict)
        
        # Evaluate the rule
        result = evaluate_rule_logic(ast, data)
        
        return jsonify({
            "message": "Rule evaluated successfully",
            "result": result,
            "evaluated_data": data,
            "rule": ast_dict
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": f"Error evaluating rule: {str(e)}",
            "details": {
                "rule": ast_dict,
                "data": data
            }
        }), 500

if __name__ == '__main__':
    app.run(debug=True)