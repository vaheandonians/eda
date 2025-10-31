# EDA - Exploratory Data Analysis with LangGraph

A LangGraph-powered data analysis pipeline that processes CSV and Excel files through automated exploratory data analysis steps.

## Features

- **File Loading**: Supports both CSV and Excel (.xlsx, .xls) files
- **Header Identification**: Automatically identifies all column headers
- **Header Normalization**: Normalizes headers to snake_case format (lowercase, underscores, no special characters)
- **Statistical Analysis**: Computes comprehensive statistics for each column:
  - For numeric columns: min, max, mean, median, std, quantiles (Q25, Q75)
  - For text columns: most common value, length statistics (min, max, average)
  - For all columns: count, null count, unique count, data type

## Graph Architecture

The application uses LangGraph to create a state-based processing pipeline:

```
START → load_file → identify_headers → normalize_headers → compute_statistics → END
```

Each node in the graph performs a specific task and updates the shared state, allowing for a clear, modular data processing workflow.

### Graph Visualization

When you run the application, it automatically generates a **Mermaid diagram** (`eda_graph.png`) that visually represents the graph structure, showing all nodes and edges. This makes it easy to understand the data flow at a glance.

## Installation

This project uses `uv` for dependency management. Make sure you have `uv` installed.

```bash
uv sync
```

## Dependencies

- **langchain**: Framework for building LLM applications
- **langgraph**: Graph-based workflow orchestration
- **pandas**: Data manipulation and analysis
- **openpyxl**: Excel file support

## Usage

### Interactive Mode

Run the main script and provide a file path when prompted:

```bash
uv run python main.py
```

When you run the script, it will:
1. **Generate a graph visualization** (`eda_graph.png`) showing the LangGraph pipeline structure
2. **Prompt you** to enter the path to your CSV or Excel file
3. **Process the file** through the graph nodes
4. **Display comprehensive results** including headers, normalization, and statistics

### Sample Data

Two sample files are included:

1. **sample_data.csv**: Employee data with 15 records
   - Contains: Employee ID, Names, Age, Department, Salary, Years of Service, Performance Score

2. **sample_data.xlsx**: Product inventory data with 8 records
   - Contains: Product ID, Product Name, Category, Price, Stock Quantity, Rating, Units Sold

### Example

```bash
$ uv run python main.py

🚀 EDA Graph with LangGraph
This graph processes CSV/Excel files through the following steps:
  1. Load file (CSV or Excel)
  2. Identify headers
  3. Normalize headers
  4. Compute statistics

Enter the path to your CSV or Excel file: sample_data.csv
```

## Output

The pipeline provides detailed output including:

- File information (path, shape)
- Original headers list
- Header normalization mapping (original → normalized)
- Comprehensive statistics for each column

### Example Output

```
================================================================================
EDA GRAPH EXECUTION RESULTS
================================================================================

📁 File: sample_data.csv
📊 Shape: (15, 8)

--------------------------------------------------------------------------------
ORIGINAL HEADERS:
--------------------------------------------------------------------------------
  • Employee ID
  • First Name
  • Last Name
  • Age
  ...

--------------------------------------------------------------------------------
NORMALIZED HEADERS MAPPING:
--------------------------------------------------------------------------------
  Employee ID                    → employee_id
  First Name                     → first_name
  Last Name                      → last_name
  Age                            → age
  ...

--------------------------------------------------------------------------------
COLUMN STATISTICS:
--------------------------------------------------------------------------------

📊 age
   Type: int64
   Count: 15 | Null: 0 | Unique: 15
   Min: 27.00 | Max: 52.00
   Mean: 37.47 | Median: 36.00
   Std: 7.58
   Q25: 32.00 | Q75: 41.50
...
```

## Project Structure

```
eda/
├── main.py                   # Main LangGraph pipeline
├── sample_data.csv          # Sample CSV file
├── sample_data.xlsx         # Sample Excel file
├── eda_graph.png            # Generated graph visualization (auto-created on run)
├── pyproject.toml           # Project configuration
├── uv.lock                  # Dependency lock file
└── README.md                # This file
```

## State Schema

The graph uses a `TypedDict` state that flows through all nodes:

```python
class EDState(TypedDict):
    file_path: str                              # Input file path
    df: Optional[pd.DataFrame]                  # Loaded DataFrame
    original_headers: Optional[List[str]]       # Original column names
    normalized_headers: Optional[Dict[str, str]] # Original → Normalized mapping
    statistics: Optional[Dict[str, Dict]]       # Column statistics
    error: Optional[str]                        # Error message if any
```

## Graph Nodes

### 1. load_file
Loads CSV or Excel file into a pandas DataFrame.

### 2. identify_headers
Extracts all column headers from the DataFrame.

### 3. normalize_headers
Normalizes header names:
- Converts to lowercase
- Replaces spaces with underscores
- Removes special characters
- Applies the normalized names to the DataFrame

### 4. compute_statistics
Calculates comprehensive statistics for each column based on data type.

## Extending the Graph

To add new nodes or modify the workflow:

1. Define a new node function that takes `EDState` and returns `Dict[str, Any]`
2. Add the node to the graph builder: `builder.add_node("node_name", node_function)`
3. Add edges to connect it: `builder.add_edge("from_node", "to_node")`

Example:

```python
def custom_analysis(state: EDState) -> Dict[str, Any]:
    df = state["df"]
    # Your custom analysis here
    return {"custom_result": result}

# Add to graph
builder.add_node("custom_analysis", custom_analysis)
builder.add_edge("compute_statistics", "custom_analysis")
builder.add_edge("custom_analysis", END)
```

## Error Handling

The graph includes error handling at each step. If an error occurs, it's stored in the state and subsequent nodes can skip processing.

## License

MIT

## Contributing

Feel free to submit issues or pull requests to improve the project.

