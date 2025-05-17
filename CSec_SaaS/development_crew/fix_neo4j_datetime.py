#!/usr/bin/env python
"""
Helper script to fix Neo4j DateTime conversion in repository.py
"""

import re
import sys

def fix_repository_file():
    """Fix Neo4j DateTime conversion in repository.py"""
    repo_path = 'infrastructure/knowledge_fabric/core/repository.py'
    
    # Read the repository file
    with open(repo_path, 'r') as f:
        content = f.read()
    
    # Fix single object conversions
    pattern1 = r'self\.model_class\(\*\*result\[0\]\[\'n\'\]\)'
    repl1 = r'self.model_class(**convert_neo4j_to_python(result[0][\'n\']))'
    content = re.sub(pattern1, repl1, content)
    
    # Fix conversions using dict() first
    pattern2 = r'self\.model_class\(\*\*dict\(result\[0\]\[\'n\'\]\)\)'
    repl2 = r'self.model_class(**convert_neo4j_to_python(result[0][\'n\']))'
    content = re.sub(pattern2, repl2, content)
    
    # Fix _convert_neo4j_types usages
    pattern3 = r'node_data = self\._convert_neo4j_types\(dict\(result\[0\]\[\'n\'\]\)\)'
    repl3 = r'node_data = convert_neo4j_to_python(result[0][\'n\'])'
    content = re.sub(pattern3, repl3, content)
    
    # Fix list comprehensions
    pattern4 = r'return \[self\.model_class\(\*\*record\[\'([a-z])\'\]\) for record in result if \'([a-z])\' in record\]'
    repl4 = r'return [self.model_class(**convert_neo4j_to_python(record[\'\1\'])) for record in result if \'\2\' in record]'
    content = re.sub(pattern4, repl4, content)
    
    # Fix other specific model class instantiations
    pattern5 = r'([A-Za-z]+Model)\(\*\*record\[\'([a-z])\'\]\)'
    repl5 = r'\1(**convert_neo4j_to_python(record[\'\2\']))'
    content = re.sub(pattern5, repl5, content)
    
    # Write the updated content back to the file
    with open(repo_path, 'w') as f:
        f.write(content)
    
    print("✅ Successfully updated repository.py to fix Neo4j DateTime conversion issues")

if __name__ == "__main__":
    fix_repository_file()
