from langchain_core.runnables.graph_mermaid import draw_mermaid, draw_mermaid_png

def visualize_graph(graph, output_file=None):
    """
    Visualize the graph using Mermaid.ink API
    Args:
        graph: Your LangGraph graph
        output_file: Optional path to save the PNG
    Returns:
        bytes: PNG image bytes if output_file is None
        str: Path to saved file if output_file is provided
    """
    # Get the graph object
    graph_obj = graph.get_graph()

    # Check if draw_mermaid method exists (newer API)
    if hasattr(graph_obj, 'draw_mermaid'):
        # Use the draw_mermaid method directly
        mermaid_syntax = graph_obj.draw_mermaid()
    else:
        # Fall back to using the graph directly with draw_mermaid function
        mermaid_syntax = draw_mermaid(graph)

    # Convert to PNG using Mermaid.ink API
    img_bytes = draw_mermaid_png(
        mermaid_syntax=mermaid_syntax,
        output_file_path=output_file,
        draw_method="API",  # Use Mermaid.ink API
        background_color="white",
        padding=10
    )

    return output_file if output_file else img_bytes