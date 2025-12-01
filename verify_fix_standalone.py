import re
from typing import List, Optional

# Copying the class directly to avoid dependency issues
class QueryTemplates:
    """
    Template-based SQL generation for common query patterns.
    Matches questions to templates and fills in parameters.
    """
    
    def __init__(self):
        self.templates = self._init_templates()
    
    def _init_templates(self) -> dict:
        """Initialize query templates"""
        return {
            # Average vital sign
            'avg_vital_sign': {
                'patterns': [
                    r'average.*(heart rate|blood pressure|temperature|weight)',
                    r'avg.*(hr|bp|temp)'
                ],
                'sql': "SELECT AVG(JSON_EXTRACT(vital_signs, '$.{field}')) as avg_{field} FROM visits WHERE vital_signs IS NOT NULL;",
                'params': ['field'],
                'field_mapping': {
                    'heart rate': 'heart_rate',
                    'hr': 'heart_rate',
                    'blood pressure': 'blood_pressure_systolic',
                    'bp': 'blood_pressure_systolic',
                    'temperature': 'temperature',
                    'temp': 'temperature',
                    'weight': 'weight'
                }
            }
        }
    
    def match(self, question: str) -> Optional[str]:
        """
        Try to match question to a template and generate SQL.
        Returns SQL if match found, None otherwise.
        """
        question_lower = question.lower().strip()
        
        for template_name, template_data in self.templates.items():
            for pattern in template_data['patterns']:
                match = re.search(pattern, question_lower)
                
                if match:
                    # Extract parameters from regex groups
                    params = {}
                    if template_data['params']:
                        for i, param_name in enumerate(template_data['params'], 1):
                            if i <= len(match.groups()):
                                param_value = match.group(i)
                                
                                # Handle field mapping if exists
                                if param_name == 'field' and 'field_mapping' in template_data:
                                    # Find which field was mentioned
                                    for key, value in template_data['field_mapping'].items():
                                        if key in question_lower:
                                            param_value = value
                                            break
                                
                                params[param_name] = param_value
                    
                    # Fill template with parameters
                    sql = template_data['sql'].format(**params) if params else template_data['sql']
                    
                    return sql
        
        return None

def test_template_fix():
    qt = QueryTemplates()
    question = "What's the average heart rate across all visits?"
    
    print(f"Testing question: '{question}'")
    sql = qt.match(question)
    print(f"Generated SQL: {sql}")
    
    if "{field}" in sql:
        print("❌ FAILURE: {field} placeholder was not replaced.")
    else:
        print("✅ SUCCESS: {field} was replaced.")
        if "heart_rate" in sql:
             print("✅ SUCCESS: Correct field 'heart_rate' used.")

if __name__ == "__main__":
    test_template_fix()
