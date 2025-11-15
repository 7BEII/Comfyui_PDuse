import { app } from "/scripts/app.js";
import { api } from "/scripts/api.js";

app.registerExtension({
    name: "PDuse.ShowGif",
    
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name !== "PD_ImageListToGif") return;

        // 参考VideoHelperSuite的实现方式
        // 在onNodeCreated时创建预览widget，而不是在onExecuted时
        const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function() {
            const r = originalOnNodeCreated ? originalOnNodeCreated.apply(this, arguments) : undefined;
            
            // 创建预览容器
            const previewNode = this;
            const element = document.createElement("div");
            element.style.width = "100%";
            
            // 添加DOMWidget（参考VHS的方式）
            const previewWidget = this.addDOMWidget("videopreview", "preview", element, {
                serialize: false,
                hideOnZoom: false,
            });
            
            // 实现computeSize方法（关键！参考VHS）
            previewWidget.computeSize = function(width) {
                if (this.aspectRatio && !this.parentEl.hidden) {
                    // 根据节点宽度和宽高比计算高度
                    let height = (previewNode.size[0] - 20) / this.aspectRatio + 10;
                    if (!(height > 0)) {
                        height = 0;
                    }
                    this.computedHeight = height + 10;
                    return [width, height];
                }
                return [width, -4]; // 没有加载内容时，widget不显示
            };
            
            // 创建父容器
            previewWidget.parentEl = document.createElement("div");
            previewWidget.parentEl.className = "pduse_preview";
            previewWidget.parentEl.style.width = "100%";
            previewWidget.parentEl.style.padding = "4px";
            previewWidget.parentEl.style.boxSizing = "border-box";
            previewWidget.parentEl.hidden = true; // 初始隐藏
            element.appendChild(previewWidget.parentEl);
            
            // 创建video元素（用于MP4预览）
            previewWidget.videoEl = document.createElement("video");
            previewWidget.videoEl.controls = true;
            previewWidget.videoEl.loop = true;
            previewWidget.videoEl.muted = true;
            previewWidget.videoEl.autoplay = false;
            previewWidget.videoEl.style.width = "100%";
            previewWidget.videoEl.hidden = true;
            
            // 创建img元素（用于GIF/WebP预览）
            previewWidget.imgEl = document.createElement("img");
            previewWidget.imgEl.style.width = "100%";
            previewWidget.imgEl.hidden = true;
            
            // 创建格式标签
            previewWidget.labelEl = document.createElement("div");
            previewWidget.labelEl.style.fontSize = "10px";
            previewWidget.labelEl.style.color = "#888";
            previewWidget.labelEl.style.textAlign = "center";
            previewWidget.labelEl.style.marginTop = "4px";
            
            // 添加元素到容器
            previewWidget.parentEl.appendChild(previewWidget.videoEl);
            previewWidget.parentEl.appendChild(previewWidget.imgEl);
            previewWidget.parentEl.appendChild(previewWidget.labelEl);
            
            // 添加事件传递（参考VHS，防止预览元素拦截节点操作）
            element.addEventListener('contextmenu', (e) => {
                e.preventDefault();
                return app.canvas._mousedown_callback(e);
            }, true);
            element.addEventListener('pointerdown', (e) => {
                e.preventDefault();
                return app.canvas._mousedown_callback(e);
            }, true);
            element.addEventListener('mousewheel', (e) => {
                e.preventDefault();
                return app.canvas._mousewheel_callback(e);
            }, true);
            element.addEventListener('pointermove', (e) => {
                e.preventDefault();
                return app.canvas._mousemove_callback(e);
            }, true);
            element.addEventListener('pointerup', (e) => {
                e.preventDefault();
                return app.canvas._mouseup_callback(e);
            }, true);
            
            // 添加fitHeight辅助函数（参考VHS）
            const fitHeight = () => {
                previewNode.setSize([previewNode.size[0], previewNode.computeSize([previewNode.size[0], previewNode.size[1]])[1]]);
                previewNode?.graph?.setDirtyCanvas(true);
            };
            
            // 视频加载事件
            previewWidget.videoEl.addEventListener("loadedmetadata", () => {
                console.log("Video loaded successfully");
                // 计算宽高比
                previewWidget.aspectRatio = previewWidget.videoEl.videoWidth / previewWidget.videoEl.videoHeight;
                previewWidget.parentEl.hidden = false;
                fitHeight();
            });
            
            previewWidget.videoEl.addEventListener("error", (e) => {
                console.error("Video load error:", e);
                previewWidget.parentEl.hidden = true;
                fitHeight();
            });
            
            // 图片加载事件
            previewWidget.imgEl.onload = () => {
                console.log("Image loaded successfully");
                // 计算宽高比
                previewWidget.aspectRatio = previewWidget.imgEl.naturalWidth / previewWidget.imgEl.naturalHeight;
                previewWidget.parentEl.hidden = false;
                fitHeight();
            };
            
            previewWidget.imgEl.onerror = (e) => {
                console.error("Image load error:", e);
                previewWidget.parentEl.hidden = true;
                fitHeight();
            };
            
            // 图片点击事件
            previewWidget.imgEl.onclick = () => {
                if (previewWidget.currentUrl) {
                    window.open(previewWidget.currentUrl, "_blank");
                }
            };
            
            // 添加updateSource方法（参考VHS）
            previewWidget.updateSource = function(params) {
                if (!params) return;
                
                console.log("PDuse Preview - updating source:", params);
                
                // 构建URL
                let url;
                if (params.subfolder) {
                    url = api.apiURL(`/view?filename=${encodeURIComponent(params.filename)}&subfolder=${encodeURIComponent(params.subfolder)}&type=${params.type || 'output'}&rand=${Math.random()}`);
                } else {
                    url = api.apiURL(`/view?filename=${encodeURIComponent(params.filename)}&type=${params.type || 'output'}&rand=${Math.random()}`);
                }
                
                previewWidget.currentUrl = url;
                
                // 根据格式类型显示对应元素
                const isVideo = params.format && params.format.startsWith('video/');
                
                if (isVideo) {
                    // 显示video，隐藏img
                    previewWidget.videoEl.hidden = false;
                    previewWidget.imgEl.hidden = true;
                    previewWidget.videoEl.src = url;
                    previewWidget.labelEl.textContent = `Format: ${params.format}`;
                } else {
                    // 显示img，隐藏video
                    previewWidget.videoEl.hidden = true;
                    previewWidget.imgEl.hidden = false;
                    previewWidget.imgEl.src = url;
                    previewWidget.labelEl.textContent = `Format: ${params.format || 'image/gif'}`;
                }
            };
            
            // 禁用默认图片预览
            this.imgs = null;
            this.imageIndex = null;
            
            return r;
        };
        
        // 重写onExecuted方法（参考VHS的实现）
        const originalOnExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function(message) {
            console.log("PDuse Preview - onExecuted message:", message);
            
            // 禁用默认预览
            this.imgs = null;
            this.imageIndex = null;
            
            // 检查是否有gifs数据
            if (message?.gifs && Array.isArray(message.gifs) && message.gifs.length > 0) {
                const gifInfo = message.gifs[0];
                console.log("PDuse Preview - gifInfo:", gifInfo);
                
                // 找到预览widget
                const previewWidget = this.widgets?.find(w => w.name === "videopreview");
                if (previewWidget && previewWidget.updateSource) {
                    previewWidget.updateSource(gifInfo);
                } else {
                    console.warn("PDuse Preview - previewWidget not found or updateSource not available");
                }
            }
            
            // 不调用原始的onExecuted，避免触发默认图片预览
            // originalOnExecuted?.apply(this, arguments);
        };
        
        // 覆盖onDrawForeground和onDrawBackground，防止默认图片渲染
        const originalOnDrawForeground = nodeType.prototype.onDrawForeground;
        nodeType.prototype.onDrawForeground = function(ctx) {
            this.imgs = null;
            this.imageIndex = null;
            return;
        };
        
        const originalOnDrawBackground = nodeType.prototype.onDrawBackground;
        nodeType.prototype.onDrawBackground = function(ctx) {
            this.imgs = null;
            this.imageIndex = null;
            return;
        };
    }
});
