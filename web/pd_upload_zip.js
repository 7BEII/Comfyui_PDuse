import { app } from "/scripts/app.js";
import { api } from "/scripts/api.js";

async function fetchApiCompat(path, options) {
    if (api?.fetchApi) {
        return api.fetchApi(path, options);
    }
    return fetch(path, options);
}

function buildUploadedFilename(data) {
    if (!data) return "";
    if (data.subfolder) {
        return `${data.subfolder}/${data.name}`;
    }
    return data.name ?? "";
}

function addZipUploadButton(node) {
    const widgetName = "zip_file_upload";

    if (!node?.widgets) return false;
    const widget = node.widgets.find((w) => w?.name === widgetName);
    if (!widget) return false;

    if (node.widgets.some((w) => w?.name === "pd_zip_upload_button")) {
        return true;
    }

    const uploadWidget = node.addWidget(
        "button",
        "choose zip file to upload",
        "image",
        () => {
            const fileInput = document.createElement("input");
            Object.assign(fileInput, {
                type: "file",
                accept: ".zip,application/zip",
                style: "display: none",
            });

            fileInput.onchange = async () => {
                if (!fileInput.files?.length) return;

                const file = fileInput.files[0];
                const formData = new FormData();
                formData.append("image", file);
                formData.append("type", "input");
                formData.append("overwrite", "true");

                const originalLabel = uploadWidget.label;
                uploadWidget.label = "Uploading...";

                try {
                    const resp = await fetchApiCompat("/upload/image", {
                        method: "POST",
                        body: formData,
                    });

                    if (resp.status === 200) {
                        const data = await resp.json();
                        const filename = buildUploadedFilename(data);
                        if (filename) {
                            widget.value = filename;
                            widget.callback?.(filename);
                        }
                        uploadWidget.label = "Upload Success";
                        setTimeout(() => {
                            uploadWidget.label = originalLabel;
                        }, 1500);
                    } else {
                        alert("Upload failed: " + resp.statusText);
                        uploadWidget.label = "Upload Failed";
                        setTimeout(() => {
                            uploadWidget.label = originalLabel;
                        }, 1500);
                    }
                } catch (error) {
                    alert("Upload error: " + error);
                    uploadWidget.label = "Upload Error";
                    setTimeout(() => {
                        uploadWidget.label = originalLabel;
                    }, 1500);
                } finally {
                    fileInput.remove();
                    app.graph?.setDirtyCanvas(true, false);
                }
            };

            document.body.appendChild(fileInput);
            fileInput.click();
        },
        { serialize: false }
    );

    uploadWidget.name = "pd_zip_upload_button";
    return true;
}

app.registerExtension({
    name: "PDuse.UploadZip",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "PD_LoadImagesFromZip" || nodeData.name === "PD_LoadTextsFromZip") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

                const maxTries = 20;
                let tries = 0;
                const tryAttach = () => {
                    tries += 1;
                    if (addZipUploadButton(this) || tries >= maxTries) return;
                    requestAnimationFrame(tryAttach);
                };
                tryAttach();
                return r;
            };
        }
    },
});

