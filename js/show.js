import { app } from "/scripts/app.js";
import { ComfyWidgets } from "/scripts/widgets.js";

const isGifNode = (nodeData) => nodeData.name === "PD_ImageListToGif";

const buildWidget = ({ node, widgetName, type, opts }) => {
	return ComfyWidgets[type](node, widgetName, [type, opts], app).widget;
};

const createImagePreview = (src) => {
	const img = document.createElement("img");
	img.src = src;
	img.width = 240;
	img.height = 240;
	img.style.objectFit = "contain";
	img.style.border = "1px solid rgba(255, 255, 255, 0.15)";
	img.style.marginTop = "6px";
	return img;
};

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

		if (isGifNode(nodeData)) {
			const originalOnExecuted = nodeType.prototype.onExecuted;
			nodeType.prototype.onExecuted = function (message) {
				originalOnExecuted?.apply(this, arguments);
				if (!message?.filepath) return;
				if (this._gifPreview) {
					this.widgets?.forEach((w) => w.onRemove?.());
					this._gifPreview = null;
				}
				const url = "/output/" + message.filepath.split(")').join("/output/")
 