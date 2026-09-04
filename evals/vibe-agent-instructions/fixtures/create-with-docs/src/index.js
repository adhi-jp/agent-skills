export function summarize(widgets) {
  return widgets.map((widget) => `${widget.id}: ${widget.name}`).join("\n");
}
