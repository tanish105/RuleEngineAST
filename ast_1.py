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

# Function to parse individual rule strings into an AST
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

# Example usage
if __name__ == "__main__":
    rule1 = "age > 30 AND department = 'Sales'"
    rule2 = "salary > 50000 OR experience > 5"

    combined_ast = combine_rules([rule1, rule2])
    print(combined_ast.to_dict())
