import { app } from "/scripts/app.js";
import { ComfyWidgets } from "/scripts/widgets.js";

function populate(text) {
	if (this.widgets) {
		const pos = this.widgets.findIndex((w) => w.name === "text");
		if (pos !== -1) {
			for (let i = pos; i < this.widgets.length; i++) {
				this.widgets[i].onRemove?.();
			}
			this.widgets.length = pos;
		}
	}

    // 兼容列表和字符串
    const v = Array.isArray(text) ? text.join("\n") : text;

	const w = ComfyWidgets["STRING"](this, "text", ["STRING", { multiline: true }], app).widget;
	w.inputEl.readOnly = true;
	w.inputEl.style.opacity = 0.6;
	w.value = v;
    
    requestAnimationFrame(() => {
        const sz = this.computeSize();
        if (sz[0] < this.size[0]) {
            sz[0] = this.size[0];
        }
        if (sz[1] < this.size[1]) {
            sz[1] = this.size[1];
        }
        this.onResize?.(sz);
        app.graph.setDirtyCanvas(true, false);
    });
}

app.registerExtension({
	name: "PDuse.ShowText",
	async beforeRegisterNodeDef(nodeType, nodeData, app) {
		if (nodeData.name === "PD_ShowText") {
			const originalOnExecuted = nodeType.prototype.onExecuted;
			nodeType.prototype.onExecuted = function (message) {
				originalOnExecuted?.apply(this, arguments);
				if (message?.text) {
					populate.call(this, message.text);
				}
			};
		}
	},
});
