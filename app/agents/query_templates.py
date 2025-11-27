import re
from typing import List, Optional
class QueryTemplates:
    """
    Template-based SQL generation for common query patterns.
    Matches questions to templates and fills in parameters.
    """
    
    def __init__(self):
        self.templates = self._init_templates()
    
    def _init_templates(self) -> dict[str, dict]:
        """Initialize query templates"""
        return {
            # Visit count by timeframe
            'visits_count_days': {
                'patterns': [
                    r'how many visits.*(?:in|during|over).*(?:last|past)\s+(\d+)\s+days?',
                    r'visits.*count.*(\d+)\s+days?',
                    r'number of visits.*(\d+)\s+days?'
                ],
                'sql': "SELECT COUNT(*) as visit_count FROM visits WHERE visit_date >= DATE_SUB(NOW(), INTERVAL {days} DAY);",
                'params': ['days']
            },
            
            # Average visit duration
            'avg_visit_duration': {
                'patterns': [
                    r'average.*visit.*duration',
                    r'avg.*visit.*time',
                    r'mean.*visit.*length'
                ],
                'sql': "SELECT AVG(duration_minutes) as avg_duration_minutes FROM visits WHERE duration_minutes IS NOT NULL;",
                'params': []
            },
            
            # Patient count
            'patient_count': {
                'patterns': [
                    r'how many patients',
                    r'total.*patients',
                    r'number of patients',
                    r'patient count'
                ],
                'sql': "SELECT COUNT(*) as patient_count FROM patients;",
                'params': []
            },
            
            # Most visits by patient
            'most_visits_patient': {
                'patterns': [
                    r'which patient.*most visits',
                    r'patient.*most.*visits',
                    r'who.*most visits'
                ],
                'sql': """SELECT p.first_name, p.last_name, p.patient_id, COUNT(v.id) as visit_count 
                         FROM patients p 
                         JOIN visits v ON p.id = v.patient_id 
                         GROUP BY p.id 
                         ORDER BY visit_count DESC 
                         LIMIT 1;""",
                'params': []
            },
            
            # Visit type distribution
            'visit_type_count': {
                'patterns': [
                    r'how many.*(?:urgent|routine|follow-up|consultation).*visits',
                    r'count.*visit.*type',
                    r'visits by type'
                ],
                'sql': "SELECT visit_type, COUNT(*) as count FROM visits GROUP BY visit_type ORDER BY count DESC;",
                'params': []
            },
            
            # Average vital sign
            'avg_vital_sign': {
                'patterns': [
                    r'average.*(?:heart rate|blood pressure|temperature|weight)',
                    r'avg.*(?:hr|bp|temp)'
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
            },
            
            # Patients without recent visits
            'inactive_patients': {
                'patterns': [
                    r'patients.*(?:haven\'t|have not|no).*visit.*(\d+)\s+days',
                    r'inactive.*patients.*(\d+)\s+days'
                ],
                'sql': """SELECT p.patient_id, p.first_name, p.last_name, MAX(v.visit_date) as last_visit
                         FROM patients p
                         LEFT JOIN visits v ON p.id = v.patient_id
                         GROUP BY p.id
                         HAVING last_visit IS NULL OR last_visit < DATE_SUB(NOW(), INTERVAL {days} DAY)
                         ORDER BY last_visit;""",
                'params': ['days']
            },
            
            # Common diagnoses
            'common_diagnoses': {
                'patterns': [
                    r'most common.*diagnos',
                    r'top.*diagnos',
                    r'frequent.*diagnos'
                ],
                'sql': """SELECT diagnosis, COUNT(*) as count 
                         FROM visits 
                         WHERE diagnosis IS NOT NULL AND diagnosis != ''
                         GROUP BY diagnosis 
                         ORDER BY count DESC 
                         LIMIT 10;""",
                'params': []
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
    
    def get_supported_patterns(self) -> List[str]:
        """Get list of supported query patterns"""
        patterns = []
        for template_name, template_data in self.templates.items():
            patterns.extend(template_data['patterns'])
        return patterns