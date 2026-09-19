"""
visualize.py - render a TegoGraph as an interactive HTML graph (pyvis).

Output is a single self-contained-ish HTML file (pyvis inlines vis.js from
a CDN) with draggable nodes, zoom/pan, physics layout, and a hover tooltip
showing every property a transform attached to that entity.
"""

from __future__ import annotations
from typing import Optional

from pyvis.network import Network

from .graph import TegoGraph


def _tooltip(entity) -> str:
    lines = [f"<b>{entity.TYPE}</b>: {entity.value}"]
    for k, v in entity.properties.items():
        lines.append(f"{k}: {v}")
    if entity.notes:
        lines.append("notes: " + "; ".join(entity.notes))
    return "<br>".join(str(x) for x in lines)


def render_html(graph: TegoGraph, out_path: str, title: str = "TegoScent Graph") -> str:
    net = Network(
        height="900px",
        width="100%",
        directed=True,
        bgcolor="#111318",
        font_color="#eaeaea",
        notebook=False,
    )
    net.barnes_hut(gravity=-8000, spring_length=140, spring_strength=0.02, damping=0.35)

    for entity in graph.entities():
        net.add_node(
            entity.id,
            label=entity.value[:40],
            title=_tooltip(entity),
            color=entity.COLOR,
            shape="dot",
            size=18,
        )

    for u, v, data in graph.nx.edges(data=True):
        net.add_edge(u, v, title=data.get("transform", ""), label=data.get("label", ""), arrows="to")

    net.set_options("""
    {
      "edges": {"color": {"color": "#4a4f5c", "highlight": "#ffffff"}, "smooth": {"type": "dynamic"}},
      "interaction": {"hover": true, "tooltipDelay": 120},
      "physics": {"stabilization": {"iterations": 200}}
    }
    """)

    net.write_html(out_path, notebook=False, open_browser=False)
    return out_path
