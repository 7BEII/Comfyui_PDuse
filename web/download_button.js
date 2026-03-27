import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

app.registerExtension({
    name: "PDTool.ZipPackingsave",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "PD_ZIP_Packingsave") {
            const onExecuted = nodeType.prototype.onExecuted;

            // 劫持节点的执行完毕事件
            nodeType.prototype.onExecuted = function (message) {
                onExecuted?.apply(this, arguments);

                // 如果后端传来了 zip 信号
                if (message && message.zip && message.zip.length > 0) {
                    const zipData = message.zip[0];

                    // 组装调用 ComfyUI 下载接口的 URL
                    let downloadParams = new URLSearchParams({
                        filename: zipData.filename,
                        type: zipData.type,
                    });
                    if (zipData.subfolder) {
                        downloadParams.append("subfolder", zipData.subfolder);
                    }
                    const downloadUrl = api.apiURL("/view?" + downloadParams.toString());

                    // 检查节点上是否已经有了我们自己加的下载按钮
                    let downloadWidget = this.widgets?.find(w => w.name === "download_zip_btn");

                    if (!downloadWidget) {
                        // 如果没有，就在节点上创建一个新的按钮
                        downloadWidget = this.addWidget("button", "download_zip_btn", "📥 Download ZIP", () => {
                            // 点击按钮时，利用创建 a 标签的黑魔法触发浏览器原生的下载行为
                            const a = document.createElement("a");
                            a.href = downloadUrl;
                            a.download = zipData.filename; // 默认下载名
                            document.body.appendChild(a);
                            a.click();
                            document.body.removeChild(a);
                        });
                    } else {
                        // 如果按钮已经有了（比如连续生成），只需更新点击事件里绑定的新文件名即可
                        downloadWidget.callback = () => {
                            const a = document.createElement("a");
                            a.href = downloadUrl;
                            a.download = zipData.filename;
                            document.body.appendChild(a);
                            a.click();
                            document.body.removeChild(a);
                        }
                    }

                    // 强制刷新节点UI尺寸
                    this.onResize?.(this.size);
                }
            };
        }
    }
});
