class Node:
    def __init__(self, node_type, value=None, left=None, right=None):
        self.node_type = node_type  # "operator" or "operand"
        self.value = value  # Value for operand nodes (e.g., comparisons)
        self.left = left  # Left child
        self.right = right  # Right child
    
    def to_dict(self):
        return {
            "node_type": self.node_type,
            "value": self.value,
            "left": self.left.to_dict() if self.left else None,
            "right": self.right.to_dict() if self.right else None
        }
    
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

def parse_rule_string(rule_string):
    rule_string = rule_string.strip()
    
    def find_main_operator(s):
        balance = 0
        i = 0
        while i < len(s):
            char = s[i]
            if char == '(':
                balance += 1
            elif char == ')':
                balance -= 1
            elif balance == 0:
                if s[i:].startswith('AND'):
                    return i, 'AND'
                elif s[i:].startswith('OR'):
                    return i, 'OR'
            i += 1
        return -1, None

    # Remove outer parentheses if they exist
    while rule_string.startswith('(') and rule_string.endswith(')'):
        # Check if these parentheses are actually matching
        balance = 0
        all_balanced = True
        for i, char in enumerate(rule_string[:-1]):  # Exclude the last character
            if char == '(':
                balance += 1
            elif char == ')':
                balance -= 1
            if balance == 0 and i != len(rule_string) - 2:
                all_balanced = False
                break
        if all_balanced:
            rule_string = rule_string[1:-1].strip()
        else:
            break

    op_index, operator = find_main_operator(rule_string)
    
    if operator:
        left_expr = rule_string[:op_index].strip()
        right_expr = rule_string[op_index + len(operator):].strip()
        
        # Recursively parse left and right expressions
        left_node = parse_rule_string(left_expr)
        right_node = parse_rule_string(right_expr)
        
        return Node(node_type="operator", value=operator, left=left_node, right=right_node)
    
    # If no operator is found, this is a leaf node (operand)
    return Node(node_type="operand", value=rule_string)

# Function to combine multiple rules into a single AST
def combine_rules(rules):
    if not rules:
        return None
    
    # Parse each rule into an AST
    ast_list = [parse_rule_string(rule) for rule in rules]
    
    # For rules involving department or role conditions, we should use OR
    # For other conditions like salary and experience, we can use AND
    def has_department_condition(node):
        if node.node_type == "operand":
            return "department" in node.value
        return (node.left and has_department_condition(node.left)) or \
               (node.right and has_department_condition(node.right))
    
    # Group rules by whether they contain department conditions
    department_rules = []
    other_rules = []
    for ast in ast_list:
        if has_department_condition(ast):
            department_rules.append(ast)
        else:
            other_rules.append(ast)
    
    # Combine department rules with OR
    if department_rules:
        department_combined = department_rules[0]
        for ast in department_rules[1:]:
            department_combined = Node(node_type="operator", value="OR", 
                                    left=department_combined, right=ast)
    else:
        department_combined = None
    
    # Combine other rules with AND
    if other_rules:
        other_combined = other_rules[0]
        for ast in other_rules[1:]:
            other_combined = Node(node_type="operator", value="AND", 
                                left=other_combined, right=ast)
    else:
        other_combined = None
    
    # Finally combine both groups
    if department_combined and other_combined:
        return Node(node_type="operator", value="AND", 
                   left=department_combined, right=other_combined)
    return department_combined or other_combined

# Function to evaluate rules with a dictionary data
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
            if len(parts) < 3:
                raise ValueError(f"Invalid operand format: {node.value}")
                
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
            
            # Type conversion and validation
            try:
                # If comparison value is numeric, both values should be numeric
                if comparison_value.replace('.', '').isdigit():
                    if not isinstance(actual_value, (int, float)):
                        try:
                            actual_value = float(actual_value)
                        except (ValueError, TypeError):
                            return False
                    comparison_value = float(comparison_value)
                else:
                    # For string comparisons, convert both to strings
                    actual_value = str(actual_value)
                    comparison_value = str(comparison_value)
            except (ValueError, TypeError):
                return False
            
            # Perform the comparison
            try:
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
            except TypeError:
                # If comparison can't be performed (e.g., comparing string with number)
                return False
        
        return False

    return evaluate_node(ast)