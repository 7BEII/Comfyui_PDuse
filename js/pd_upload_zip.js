import { app } from "/scripts/app.js";
import { api } from "/scripts/api.js";

app.registerExtension({
    name: "PDuse.UploadZip",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "PD_LoadImagesFromZip" || nodeData.name === "PD_LoadTextsFromZip") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

                const widgetName = "zip_file_upload";
                const widget = this.widgets.find((w) => w.name === widgetName);

                if (widget) {
                    // 创建上传按钮
                    const uploadWidget = this.addWidget("button", "choose zip file to upload", "upload", () => {
                        const fileInput = document.createElement("input");
                        Object.assign(fileInput, {
                            type: "file",
                            accept: ".zip,application/zip",
                            style: "display: none",
                            onchange: async () => {
                                if (fileInput.files.length) {
                                    const file = fileInput.files[0];
                                    const formData = new FormData();
                                    formData.append("image", file);
                                    formData.append("overwrite", "true");

                                    try {
                                        uploadWidget.name = "Uploading...";
                                        
                                        const resp = await api.fetchApi("/upload/image", {
                                            method: "POST",
                                            body: formData,
                                        });

                                        if (resp.status === 200) {
                                            const data = await resp.json();
                                            // data.name 是文件名，如果有子目录可能包含路径
                                            widget.value = data.name;
                                            uploadWidget.name = "Upload Success";
                                            setTimeout(() => {
                                                uploadWidget.name = "choose zip file to upload";
                                            }, 2000);
                                        } else {
                                            alert("Upload failed: " + resp.statusText);
                                            uploadWidget.name = "Upload Failed";
                                            setTimeout(() => {
                                                uploadWidget.name = "choose zip file to upload";
                                            }, 2000);
                                        }
                                    } catch (error) {
                                        alert("Upload error: " + error);
                                        uploadWidget.name = "Upload Error";
                                        setTimeout(() => {
                                            uploadWidget.name = "choose zip file to upload";
                                        }, 2000);
                                    }
                                }
                            },
                        });
                        document.body.appendChild(fileInput);
                        fileInput.click();
                        document.body.removeChild(fileInput);
                    });
                }
                return r;
            };
        }
    },
});

