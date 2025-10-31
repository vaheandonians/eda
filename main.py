from typing import TypedDict, Optional, Dict, Any, List, Annotated
from pathlib import Path
import pandas as pd
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send


def merge_statistics(existing: Optional[Dict[str, Dict[str, Any]]], new: Optional[Dict[str, Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
    if existing is None:
        existing = {}
    if new is None:
        return existing
    return {**existing, **new}


class EDState(TypedDict):
    file_path: str
    df: Optional[pd.DataFrame]
    original_headers: Optional[List[str]]
    normalized_headers: Optional[Dict[str, str]]
    statistics: Annotated[Optional[Dict[str, Dict[str, Any]]], merge_statistics]
    error: Optional[str]


class ColumnAnalysisState(TypedDict):
    file_path: str
    df: Optional[pd.DataFrame]
    original_headers: Optional[List[str]]
    normalized_headers: Optional[Dict[str, str]]
    statistics: Annotated[Optional[Dict[str, Dict[str, Any]]], merge_statistics]
    error: Optional[str]
    column_name: str


def load_file(state: EDState) -> Dict[str, Any]:
    file_path = state["file_path"]
    path = Path(file_path)
    
    if not path.exists():
        return {"error": f"File not found: {file_path}"}
    
    try:
        if path.suffix.lower() == '.csv':
            df = pd.read_csv(file_path)
        elif path.suffix.lower() in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        else:
            return {"error": f"Unsupported file format: {path.suffix}. Use CSV or Excel files."}
        
        return {"df": df, "error": None}
    except Exception as e:
        return {"error": f"Error loading file: {str(e)}"}


def identify_headers(state: EDState) -> Dict[str, Any]:
    if state.get("error"):
        return {}
    
    df = state["df"]
    if df is None:
        return {"error": "No dataframe available"}
    
    headers = df.columns.tolist()
    return {"original_headers": headers}


def normalize_headers(state: EDState) -> Dict[str, Any]:
    if state.get("error"):
        return {}
    
    original_headers = state.get("original_headers", [])
    if not original_headers:
        return {"error": "No headers found"}
    
    normalized = {}
    for header in original_headers:
        normalized_name = str(header).lower().strip()
        normalized_name = normalized_name.replace(' ', '_')
        normalized_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in normalized_name)
        normalized_name = '_'.join(filter(None, normalized_name.split('_')))
        normalized[header] = normalized_name
    
    df = state["df"]
    df.columns = [normalized[col] for col in df.columns]
    
    return {"normalized_headers": normalized, "df": df}


def fan_out_columns(state: EDState) -> List[Send]:
    if state.get("error"):
        return []
    
    df = state["df"]
    if df is None:
        return []
    
    return [
        Send("analyze_column", {**state, "column_name": column})
        for column in df.columns
    ]


def analyze_column(state: ColumnAnalysisState) -> Dict[str, Any]:
    df = state["df"]
    column = state["column_name"]
    
    col_stats = {
        "dtype": str(df[column].dtype),
        "count": int(df[column].count()),
        "null_count": int(df[column].isnull().sum()),
        "unique_count": int(df[column].nunique())
    }
    
    if pd.api.types.is_numeric_dtype(df[column]):
        col_stats.update({
            "min": float(df[column].min()) if pd.notna(df[column].min()) else None,
            "max": float(df[column].max()) if pd.notna(df[column].max()) else None,
            "mean": float(df[column].mean()) if pd.notna(df[column].mean()) else None,
            "median": float(df[column].median()) if pd.notna(df[column].median()) else None,
            "std": float(df[column].std()) if pd.notna(df[column].std()) else None,
            "q25": float(df[column].quantile(0.25)) if pd.notna(df[column].quantile(0.25)) else None,
            "q75": float(df[column].quantile(0.75)) if pd.notna(df[column].quantile(0.75)) else None,
        })
    elif pd.api.types.is_string_dtype(df[column]) or pd.api.types.is_object_dtype(df[column]):
        non_null_values = df[column].dropna()
        if len(non_null_values) > 0:
            col_stats.update({
                "most_common": str(non_null_values.mode()[0]) if len(non_null_values.mode()) > 0 else None,
                "min_length": int(non_null_values.astype(str).str.len().min()),
                "max_length": int(non_null_values.astype(str).str.len().max()),
                "avg_length": float(non_null_values.astype(str).str.len().mean()),
            })
    
    return {"statistics": {column: col_stats}}


def aggregate_statistics(state: EDState) -> Dict[str, Any]:
    return {}


def create_eda_graph():
    builder = StateGraph(EDState)
    
    builder.add_node("load_file", load_file)
    builder.add_node("identify_headers", identify_headers)
    builder.add_node("normalize_headers", normalize_headers)
    builder.add_node("analyze_column", analyze_column)
    builder.add_node("aggregate_statistics", aggregate_statistics)
    
    builder.add_edge(START, "load_file")
    builder.add_edge("load_file", "identify_headers")
    builder.add_edge("identify_headers", "normalize_headers")
    builder.add_conditional_edges("normalize_headers", fan_out_columns, ["analyze_column"])
    builder.add_edge("analyze_column", "aggregate_statistics")
    builder.add_edge("aggregate_statistics", END)
    
    return builder.compile()


def print_results(result: EDState):
    print("\n" + "="*80)
    print("EDA GRAPH EXECUTION RESULTS")
    print("="*80)
    
    if result.get("error"):
        print(f"\n❌ ERROR: {result['error']}")
        return
    
    print(f"\n📁 File: {result['file_path']}")
    print(f"📊 Shape: {result['df'].shape if result.get('df') is not None else 'N/A'}")
    
    print("\n" + "-"*80)
    print("ORIGINAL HEADERS:")
    print("-"*80)
    for header in result.get("original_headers", []):
        print(f"  • {header}")
    
    print("\n" + "-"*80)
    print("NORMALIZED HEADERS MAPPING:")
    print("-"*80)
    for original, normalized in result.get("normalized_headers", {}).items():
        print(f"  {original:30s} → {normalized}")
    
    print("\n" + "-"*80)
    print("COLUMN STATISTICS:")
    print("-"*80)
    
    for column, stats in result.get("statistics", {}).items():
        print(f"\n📊 {column}")
        print(f"   Type: {stats['dtype']}")
        print(f"   Count: {stats['count']} | Null: {stats['null_count']} | Unique: {stats['unique_count']}")
        
        if "min" in stats:
            print(f"   Min: {stats['min']:.2f} | Max: {stats['max']:.2f}" if stats['min'] is not None else "   Min: N/A | Max: N/A")
            print(f"   Mean: {stats['mean']:.2f} | Median: {stats['median']:.2f}" if stats['mean'] is not None else "   Mean: N/A | Median: N/A")
            print(f"   Std: {stats['std']:.2f}" if stats['std'] is not None else "   Std: N/A")
            print(f"   Q25: {stats['q25']:.2f} | Q75: {stats['q75']:.2f}" if stats['q25'] is not None else "   Q25: N/A | Q75: N/A")
        elif "most_common" in stats and stats['most_common'] is not None:
            print(f"   Most Common: {stats['most_common']}")
            print(f"   Length Range: {stats['min_length']} - {stats['max_length']} (avg: {stats['avg_length']:.1f})")
    
    print("\n" + "="*80)


def main():
    graph = create_eda_graph()
    
    print("\n🚀 EDA Graph with LangGraph")
    print("This graph processes CSV/Excel files through the following steps:")
    print("  1. Load file (CSV or Excel)")
    print("  2. Identify headers")
    print("  3. Normalize headers")
    print("  4. Analyze each column in parallel ⚡")
    print("  5. Aggregate statistics")
    
    file_path = input("\nEnter the path to your CSV or Excel file: ").strip()
    
    result = graph.invoke({"file_path": file_path})
    print_results(result)


if __name__ == "__main__":
    graph = create_eda_graph()
    
    try:
        graph_image = graph.get_graph().draw_mermaid_png()
        with open("eda_graph.png", "wb") as f:
            f.write(graph_image)
        print("📊 Graph visualization saved to: eda_graph.png")
    except Exception as e:
        print(f"⚠️  Could not generate graph visualization: {e}")
        print("   (This is optional - the graph will still work)")
    
    main()
