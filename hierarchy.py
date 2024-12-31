import pandas as pd
import json
import sys
from collections import defaultdict

def read_excel(file_path):
    """
    Reads the Excel file and returns a pandas DataFrame.
    
    Args:
        file_path (str): Path to the Excel file.
        
    Returns:
        pd.DataFrame: DataFrame containing the Excel data.
    """
    try:
        df = pd.read_excel(file_path, dtype=str)  # Read all data as strings to avoid issues
        # Ensure required columns are present
        required_columns = {'Employee', 'Supervisor', 'Official'}
        if not required_columns.issubset(df.columns):
            missing = required_columns - set(df.columns)
            raise ValueError(f"Missing columns in Excel file: {', '.join(missing)}")
        # Fill NaN with None for easier handling
        df = df.where(pd.notnull(df), None)
        return df
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        sys.exit(1)

def detect_cycles(df):
    """
    Detects cycles in the supervisory relationships.
    
    Args:
        df (pd.DataFrame): DataFrame containing the Excel data.
        
    Raises:
        ValueError: If a cycle is detected in the supervisory relationships.
    """
    # Build a graph where each node is a supervisor or employee
    graph = defaultdict(list)
    for _, row in df.iterrows():
        employee = row['Employee']
        supervisor = row['Supervisor']
        if supervisor:
            graph[supervisor].append(employee)
    
    visited = set()
    rec_stack = set()
    
    def dfs(node):
        visited.add(node)
        rec_stack.add(node)
        for neighbour in graph.get(node, []):
            if neighbour not in visited:
                if dfs(neighbour):
                    return True
            elif neighbour in rec_stack:
                return True
        rec_stack.remove(node)
        return False
    
    for node in graph:
        if node not in visited:
            if dfs(node):
                raise ValueError("Cycle detected in supervisory relationships.")

def build_hierarchy(df):
    """
    Builds the hierarchical structure from the DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame containing the Excel data.
        
    Returns:
        list: List of hierarchical structures representing Officials.
    """
    hierarchy = []
    
    # Create mappings
    official_to_supervisors = defaultdict(set)
    supervisor_to_employees = defaultdict(set)
    
    # Populate the mappings
    for _, row in df.iterrows():
        employee = row['Employee']
        supervisor = row['Supervisor']
        official = row['Official']
        
        if official:
            if supervisor:
                official_to_supervisors[official].add(supervisor)
            else:
                print(f"Warning: Supervisor missing for employee '{employee}'.")
        
        if supervisor:
            supervisor_to_employees[supervisor].add(employee)
        else:
            if employee not in official_to_supervisors[official]:
                print(f"Warning: Supervisor missing for employee '{employee}'.")
    
    # Identify all officials
    officials = set(df['Official'].dropna())
    
    for official in officials:
        official_node = {
            "name": official,
            "Supervisors": []
        }
        supervisors = official_to_supervisors.get(official, set())
        if not supervisors:
            print(f"Warning: No supervisors found under official '{official}'.")
        for supervisor in supervisors:
            supervisor_node = {
                "name": supervisor,
                "Employees": []
            }
            employees = supervisor_to_employees.get(supervisor, set())
            if not employees:
                print(f"Warning: No employees found under supervisor '{supervisor}'.")
            for employee in employees:
                employee_node = {
                    "name": employee
                }
                supervisor_node["Employees"].append(employee_node)
            official_node["Supervisors"].append(supervisor_node)
        hierarchy.append(official_node)
    
    return hierarchy

def save_json(data, output_path):
    """
    Saves the data to a JSON file with proper formatting.
    
    Args:
        data (dict or list): The data to be saved as JSON.
        output_path (str): Path to the output JSON file.
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"JSON data successfully saved to '{output_path}'.")
    except Exception as e:
        print(f"Error saving JSON file: {e}")
        sys.exit(1)

def main():
    # Define input and output file paths
    input_file = 'employees.xlsx'  # Replace with your Excel file path
    output_file = 'hierarchy.json'  # Replace with your desired JSON output path
    
    # Step 1: Read the Excel File
    df = read_excel(input_file)
    
    # Step 4: Error Handling - Detect Cycles
    try:
        detect_cycles(df)
    except ValueError as ve:
        print(f"Error: {ve}")
        sys.exit(1)
    
    # Step 2: Construct Hierarchical JSON Tree
    hierarchy = build_hierarchy(df)
    
    # Step 3: Output the JSON
    save_json(hierarchy, output_file)

if __name__ == "__main__":
    main()
