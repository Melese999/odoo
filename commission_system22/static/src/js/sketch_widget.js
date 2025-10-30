/** @odoo-module **/

/*import { registry } from "@web/core/registry";
import { Component, useRef, onMounted, onWillUnmount } from "@odoo/owl";

export class CommissionSketchWidget extends Component {
    setup() {
        // refs
        this.canvasRef = useRef("canvas");
        this.containerRef = useRef("container");
        this.previewRef = useRef("preview");

        // drawing state
        this.ctx = null;
        this.isDrawing = false;
        this.currentColor = "#000000";
        this.currentWidth = 3;
        this.currentTool = "pen";
        this.exportQuality = 0.92;

        // history config
        this.maxHistory = 20;
        this.history = [];
        this.historyIndex = -1;

        // drawing state
        this._lastX = null;
        this._lastY = null;

        // flags
        this._isMounted = false;

        // Touch device detection
        this.isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;

        // Store event listeners for proper cleanup
        this._eventListeners = [];

        // bind handlers
        this._onPointerDown = this._onPointerDown.bind(this);
        this._onPointerMove = this._onPointerMove.bind(this);
        this._onPointerUp = this._onPointerUp.bind(this);
        this._onPointerCancel = this._onPointerUp.bind(this);
        this._onKeyDown = this._onKeyDown.bind(this);

        onMounted(() => this._init());
        onWillUnmount(() => this._cleanup());
    }

    // Initialize canvas and listeners
    async _init() {
        this._isMounted = true;
        const canvas = this.canvasRef.el;
        const container = this.containerRef.el;

        if (!canvas || !container) {
            console.warn("SketchWidget: canvas or container missing");
            return;
        }

        this.ctx = canvas.getContext("2d", { willReadFrequently: true });

        // Setup dimensions, high-DPI scaling
        this._syncCanvasSize();

        // Initialize white background and save initial state
        this._fillBackground('#FFFFFF');
        await this._saveState();

        // Pointer events
        canvas.style.touchAction = "none";
        this._addEventListener(canvas, "pointerdown", this._onPointerDown);
        this._addEventListener(canvas, "pointermove", this._onPointerMove);
        this._addEventListener(canvas, "pointerup", this._onPointerUp);
        this._addEventListener(canvas, "pointercancel", this._onPointerCancel);

        // Keyboard shortcuts
        this._addEventListener(window, "keydown", this._onKeyDown);

        // Setup control event listeners
        this._setupControlListeners();

        // Setup resize handling
        this._setupResizeHandling(container);

        // Update preview
        this._updatePreview();

        // Set initial focus for accessibility
        canvas.setAttribute("tabindex", "0");
        canvas.setAttribute("aria-label", "Drawing canvas");
        canvas.focus();
    }

    // Helper to add and track event listeners
    _addEventListener(element, event, handler) {
        if (element) {
            element.addEventListener(event, handler);
            this._eventListeners.push({ element, event, handler });
        }
    }

    // Setup control event listeners
    _setupControlListeners() {
        // Get the root element by climbing up from canvas
        const root = this.canvasRef.el?.closest('.o_sketch_widget');
        if (!root) return;

        // Clear button
        const clearBtn = root.querySelector(".o_sketch_clear");
        if (clearBtn) {
            clearBtn.setAttribute("aria-label", "Clear canvas");
            this._addEventListener(clearBtn, "click", () => this._onClear());
            this._addEventListener(clearBtn, "keydown", (ev) => {
                if (ev.key === "Enter" || ev.key === " ") {
                    ev.preventDefault();
                    this._onClear();
                }
            });
        }

        // Save button
        const saveBtn = root.querySelector(".o_sketch_save");
        if (saveBtn) {
            saveBtn.setAttribute("aria-label", "Save sketch");
            this._addEventListener(saveBtn, "click", () => this._onSave());
            this._addEventListener(saveBtn, "keydown", (ev) => {
                if (ev.key === "Enter" || ev.key === " ") {
                    ev.preventDefault();
                    this._onSave();
                }
            });
        }

        // Undo button
        const undoBtn = root.querySelector(".o_sketch_undo");
        if (undoBtn) {
            undoBtn.setAttribute("aria-label", "Undo");
            this._addEventListener(undoBtn, "click", () => this._onUndo());
            this._addEventListener(undoBtn, "keydown", (ev) => {
                if (ev.key === "Enter" || ev.key === " ") {
                    ev.preventDefault();
                    this._onUndo();
                }
            });
        }

        // Redo button
        const redoBtn = root.querySelector(".o_sketch_redo");
        if (redoBtn) {
            redoBtn.setAttribute("aria-label", "Redo");
            this._addEventListener(redoBtn, "click", () => this._onRedo());
            this._addEventListener(redoBtn, "keydown", (ev) => {
                if (ev.key === "Enter" || ev.key === " ") {
                    ev.preventDefault();
                    this._onRedo();
                }
            });
        }

        // Color input
        const colorInput = root.querySelector(".o_sketch_color");
        if (colorInput) {
            colorInput.setAttribute("aria-label", "Select drawing color");
            colorInput.value = this.currentColor;
            this._addEventListener(colorInput, "input", (ev) => {
                this.currentColor = ev.target.value;
                this._updatePreview();
            });
            this._addEventListener(colorInput, "change", (ev) => {
                this.currentColor = ev.target.value;
                this._updatePreview();
            });
        }

        // Width input (select element)
        const widthInput = root.querySelector(".o_sketch_width");
        if (widthInput) {
            widthInput.setAttribute("aria-label", "Select line width");
            widthInput.value = this.currentWidth;
            this._addEventListener(widthInput, "change", (ev) => {
                this.currentWidth = parseInt(ev.target.value, 10) || 1;
                this._updatePreview();
            });
        }

        // Quality input
        const qualityInput = root.querySelector(".o_sketch_quality");
        if (qualityInput) {
            qualityInput.setAttribute("aria-label", "Select export quality");
            qualityInput.value = this.exportQuality * 100;
            this._addEventListener(qualityInput, "change", (ev) => {
                this.exportQuality = parseInt(ev.target.value, 10) / 100;
            });
        }

        // Tool buttons
        const toolButtons = root.querySelectorAll(".o_sketch_tool");
        toolButtons.forEach(btn => {
            const tool = btn.dataset.tool || "pen";
            btn.setAttribute("aria-label", `${tool} tool`);
            this._addEventListener(btn, "click", (ev) => {
                this.currentTool = tool;
                // Update active state
                toolButtons.forEach(b => b.classList.remove("active"));
                ev.currentTarget.classList.add("active");
                this._updatePreview();
            });
            this._addEventListener(btn, "keydown", (ev) => {
                if (ev.key === "Enter" || ev.key === " ") {
                    ev.preventDefault();
                    btn.click();
                }
            });
        });

        // Set pen as active by default
        const penTool = root.querySelector('.o_sketch_tool[data-tool="pen"]');
        if (penTool) {
            penTool.classList.add("active");
        }

        // Initial button states
        this._updateButtonStates();
    }

    // Update preview element
    _updatePreview() {
        const preview = this.previewRef.el;
        if (preview) {
            preview.style.backgroundColor = this.currentTool === 'eraser' ? '#FFFFFF' : this.currentColor;
            preview.style.borderColor = this.currentTool === 'eraser' ? '#ccc' : this.currentColor;
            preview.style.width = `${this.currentWidth * 4}px`;
            preview.style.height = `${this.currentWidth * 4}px`;
            preview.setAttribute("aria-label", `Current tool: ${this.currentTool}, Size: ${this.currentWidth}px`);
        }
    }

    // Setup resize handling with debouncing
    _setupResizeHandling(container) {
        this._resizeObserver = new ResizeObserver(entries => {
            if (this._resizeDebounce) {
                clearTimeout(this._resizeDebounce);
            }
            this._resizeDebounce = setTimeout(() => {
                if (this._isMounted) {
                    this._syncCanvasSize(true);
                }
                this._resizeDebounce = null;
            }, 150);
        });

        if (container) {
            this._resizeObserver.observe(container);
        }
    }

    // Keyboard shortcut handler
    _onKeyDown(ev) {
        if (ev.ctrlKey || ev.metaKey) {
            switch (ev.key) {
                case 'z':
                    ev.preventDefault();
                    this._onUndo();
                    break;
                case 'y':
                    ev.preventDefault();
                    this._onRedo();
                    break;
                case 's':
                    ev.preventDefault();
                    this._onSave();
                    break;
                case 'c':
                    ev.preventDefault();
                    this._onClear();
                    break;
            }
        }
    }

    // Synchronize canvas size with container
    _syncCanvasSize(preserveContent = true) {
        const canvas = this.canvasRef.el;
        const container = this.containerRef.el;

        if (!canvas || !container || !this.ctx) return;

        const dpr = window.devicePixelRatio || 1;
        const rect = container.getBoundingClientRect();
        const cssWidth = Math.max(200, Math.floor(rect.width));
        const cssHeight = Math.max(100, Math.round(cssWidth * 0.66));

        // Check if size actually changed
        if (canvas.width === Math.round(cssWidth * dpr) &&
            canvas.height === Math.round(cssHeight * dpr)) {
            return;
        }

        // Save current content if needed
        let content = null;
        if (preserveContent && canvas.width > 0 && canvas.height > 0) {
            try {
                content = this.ctx.getImageData(0, 0, canvas.width, canvas.height);
            } catch (e) {
                console.warn("Could not get image data:", e);
            }
        }

        // Set new size
        canvas.style.width = `${cssWidth}px`;
        canvas.style.height = `${cssHeight}px`;
        canvas.width = Math.round(cssWidth * dpr);
        canvas.height = Math.round(cssHeight * dpr);

        // Reset transform for high DPI
        this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

        // Restore content if available
        if (content) {
            try {
                // Create temporary canvas to hold old content
                const tempCanvas = document.createElement('canvas');
                tempCanvas.width = content.width;
                tempCanvas.height = content.height;
                const tempCtx = tempCanvas.getContext('2d');
                tempCtx.putImageData(content, 0, 0);

                // Draw scaled content
                this.ctx.drawImage(tempCanvas, 0, 0, cssWidth, cssHeight);
            } catch (e) {
                console.warn("Could not restore content:", e);
                this._fillBackground('#FFFFFF');
            }
        } else {
            // Fill with background
            this._fillBackground('#FFFFFF');
        }
    }

    // Pointer event handlers - FIXED DRAWING LOGIC
    _onPointerDown(ev) {
        if (ev.pointerType === "mouse" && ev.button !== 0) return;

        const canvas = this.canvasRef.el;
        if (!canvas) return;

        canvas.setPointerCapture(ev.pointerId);
        this.isDrawing = true;

        const rect = canvas.getBoundingClientRect();
        const x = (ev.clientX - rect.left) * (canvas.width / rect.width);
        const y = (ev.clientY - rect.top) * (canvas.height / rect.height);

        this._lastX = x;
        this._lastY = y;

        // Start drawing immediately
        this.ctx.beginPath();
        this.ctx.moveTo(x, y);
    }

    _onPointerMove(ev) {
        if (!this.isDrawing) return;

        const canvas = this.canvasRef.el;
        if (!canvas) return;

        const rect = canvas.getBoundingClientRect();
        const x = (ev.clientX - rect.left) * (canvas.width / rect.width);
        const y = (ev.clientY - rect.top) * (canvas.height / rect.height);

        // Draw line segment
        this.ctx.lineCap = 'round';
        this.ctx.lineJoin = 'round';
        this.ctx.lineWidth = this.currentWidth;
        this.ctx.strokeStyle = this.currentTool === 'eraser' ? '#FFFFFF' : this.currentColor;

        this.ctx.beginPath();
        this.ctx.moveTo(this._lastX, this._lastY);
        this.ctx.lineTo(x, y);
        this.ctx.stroke();

        // Update last position
        this._lastX = x;
        this._lastY = y;
    }

    _onPointerUp(ev) {
        if (!this.isDrawing) return;

        const canvas = this.canvasRef.el;
        if (canvas) {
            try {
                canvas.releasePointerCapture(ev.pointerId);
            } catch (e) {
                // Ignore errors
            }
        }

        this.isDrawing = false;
        this._lastX = null;
        this._lastY = null;

        this._saveState().catch(error => {
            console.warn("Failed to save state:", error);
        });
    }

    // Memory-efficient state saving
    async _saveState() {
        const canvas = this.canvasRef.el;
        if (!canvas) return;

        try {
            const dataUrl = canvas.toDataURL("image/png");

            // If we've undone and then drew new content, truncate "future" history
            if (this.historyIndex < this.history.length - 1) {
                this.history = this.history.slice(0, this.historyIndex + 1);
            }

            this.history.push(dataUrl);
            this.historyIndex = this.history.length - 1;

            // Enforce max history length
            while (this.history.length > this.maxHistory) {
                this.history.shift();
                this.historyIndex--;
            }

            this._updateButtonStates();
        } catch (error) {
            console.warn("SketchWidget: _saveState failed", error);
            this._showNotification("Failed to save drawing state", "warning");
        }
    }

    // Update undo/redo button states
    _updateButtonStates() {
        const root = this.canvasRef.el?.closest('.o_sketch_widget');
        if (!root) return;

        const undoBtn = root.querySelector(".o_sketch_undo");
        const redoBtn = root.querySelector(".o_sketch_redo");

        if (undoBtn) {
            undoBtn.disabled = this.historyIndex <= 0;
            undoBtn.setAttribute("aria-disabled", undoBtn.disabled);
        }
        if (redoBtn) {
            redoBtn.disabled = this.historyIndex >= this.history.length - 1;
            redoBtn.setAttribute("aria-disabled", redoBtn.disabled);
        }
    }

    // Restore state from history
    _restoreState() {
        if (this.historyIndex < 0 || this.historyIndex >= this.history.length) return;

        const canvas = this.canvasRef.el;
        if (!canvas || !this.ctx) return;

        const dataUrl = this.history[this.historyIndex];
        if (!dataUrl) return;

        const img = new Image();
        img.onload = () => {
            this.ctx.clearRect(0, 0, canvas.width, canvas.height);
            this.ctx.drawImage(img, 0, 0);
            this._updateButtonStates();
        };
        img.onerror = () => {
            console.warn("Failed to load history state");
            this._fillBackground('#FFFFFF');
        };
        img.src = dataUrl;
    }

    // Fill background
    _fillBackground(color) {
        const canvas = this.canvasRef.el;
        if (!canvas || !this.ctx) return;

        this.ctx.save();
        this.ctx.setTransform(1, 0, 0, 1, 0, 0);
        this.ctx.fillStyle = color;
        this.ctx.fillRect(0, 0, canvas.width, canvas.height);
        this.ctx.restore();
    }

    // Control actions
    _onClear() {
        if (confirm("Are you sure you want to clear the canvas?")) {
            this._fillBackground('#FFFFFF');
            this._saveState().catch(error => {
                console.warn("Failed to save after clear:", error);
            });
        }
    }

    async _onSave() {
        const canvas = this.canvasRef.el;
        if (!canvas) return;

        try {
            canvas.toBlob(async (blob) => {
                try {
                    const reader = new FileReader();
                    reader.onload = async () => {
                        const base64Data = reader.result.split(',')[1];
                        if (this.props.record) {
                            await this.props.record.update({ [this.props.name]: base64Data });
                            this._showNotification("Sketch saved successfully!", "success");
                        }
                    };
                    reader.onerror = () => {
                        throw new Error("Failed to read blob data");
                    };
                    reader.readAsDataURL(blob);
                } catch (error) {
                    console.error("Save process failed:", error);
                    this._showNotification("Failed to save sketch", "danger");
                }
            }, "image/png", this.exportQuality);
        } catch (error) {
            console.error("Save failed:", error);
            this._showNotification("Failed to save sketch", "danger");
        }
    }

    _onUndo() {
        if (this.historyIndex > 0) {
            this.historyIndex--;
            this._restoreState();
        }
    }

    _onRedo() {
        if (this.historyIndex < this.history.length - 1) {
            this.historyIndex++;
            this._restoreState();
        }
    }

    // Show notification
    _showNotification(message, type = "info") {
        // In a real implementation, you might use Odoo's notification system
        console.log(`${type.toUpperCase()}: ${message}`);
        // Simple user feedback
        alert(message);
    }

    // Cleanup
    _cleanup() {
        this._isMounted = false;

        // Remove all event listeners
        this._eventListeners.forEach(({ element, event, handler }) => {
            if (element) {
                element.removeEventListener(event, handler);
            }
        });
        this._eventListeners = [];

        // Cleanup resize observer
        if (this._resizeObserver) {
            this._resizeObserver.disconnect();
            this._resizeObserver = null;
        }

        if (this._resizeDebounce) {
            clearTimeout(this._resizeDebounce);
            this._resizeDebounce = null;
        }

        // Cleanup history
        this.history = [];
        this.historyIndex = -1;
    }
}

CommissionSketchWidget.template = "SketchWidget";

CommissionSketchWidget.props = {
    record: Object,
    name: String,
};

registry.category("fields").add("commission_sketch", {
    component: CommissionSketchWidget,
});*/

/** @odoo-module **/

/*import { registry } from "@web/core/registry";
import { Component, useRef, onMounted, onWillUnmount, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class CommissionSketchWidget extends Component {
    setup() {
        // Services
        this.notification = useService("notification");

        // Refs
        this.canvasRef = useRef("canvas");
        this.containerRef = useRef("container");
        this.previewRef = useRef("preview");
        this.measurementInputRef = useRef("measurementInput");
        this.measurementUnitRef = useRef("measurementUnit");

        // State management
        this.state = useState({
            isMeasuring: false,
            currentMeasurement: "",
            measurementUnit: "cm",
            measurementPosition: { x: 0, y: 0 },
            showMeasurementInput: false,
            measurementFontSize: 16,
            measurementColor: "#0000FF"
        });

        // Drawing state
        this.ctx = null;
        this.isDrawing = false;
        this.currentColor = "#000000";
        this.currentWidth = 3;
        this.currentTool = "pen";
        this.exportQuality = 0.92;

        // History config
        this.maxHistory = 50;
        this.history = [];
        this.historyIndex = -1;

        // Drawing state
        this._lastX = null;
        this._lastY = null;

        // Measurement state
        this._measurementStartX = null;
        this._measurementStartY = null;
        this._measurementEndX = null;
        this._measurementEndY = null;
        this._isMeasuring = false;
        this._tempMeasurementLine = null;

        // High DPI configuration
        this.dpr = window.devicePixelRatio || 1;

        // Flags
        this._isMounted = false;

        // Touch device detection
        this.isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;

        // Store event listeners for proper cleanup
        this._eventListeners = [];

        // Bind handlers
        this._onPointerDown = this._onPointerDown.bind(this);
        this._onPointerMove = this._onPointerMove.bind(this);
        this._onPointerUp = this._onPointerUp.bind(this);
        this._onPointerCancel = this._onPointerUp.bind(this);
        this._onKeyDown = this._onKeyDown.bind(this);
        this._onWheel = this._onWheel.bind(this);

        onMounted(() => this._init());
        onWillUnmount(() => this._cleanup());
    }

    // Initialize canvas and listeners
    async _init() {
        this._isMounted = true;
        const canvas = this.canvasRef.el;
        const container = this.containerRef.el;

        if (!canvas || !container) {
            console.warn("SketchWidget: canvas or container missing");
            return;
        }

        this.ctx = canvas.getContext("2d", { willReadFrequently: true });

        // Setup dimensions, high-DPI scaling
        this._syncCanvasSize();

        // Initialize white background and save initial state
        this._fillBackground('#FFFFFF');
        await this._saveState();

        // Pointer events
        canvas.style.touchAction = "none";
        this._addEventListener(canvas, "pointerdown", this._onPointerDown);
        this._addEventListener(canvas, "pointermove", this._onPointerMove);
        this._addEventListener(canvas, "pointerup", this._onPointerUp);
        this._addEventListener(canvas, "pointercancel", this._onPointerCancel);

        // Wheel for measurement font size adjustment
        this._addEventListener(canvas, "wheel", this._onWheel, { passive: false });

        // Keyboard shortcuts
        this._addEventListener(window, "keydown", this._onKeyDown);

        // Setup control event listeners
        this._setupControlListeners();

        // Setup resize handling
        this._setupResizeHandling(container);

        // Update preview
        this._updatePreview();

        // Set initial focus for accessibility
        canvas.setAttribute("tabindex", "0");
        canvas.setAttribute("aria-label", "Drawing canvas");
        canvas.focus();
    }

    // Helper to add and track event listeners
    _addEventListener(element, event, handler, options) {
        if (element) {
            element.addEventListener(event, handler, options);
            this._eventListeners.push({ element, event, handler, options });
        }
    }

    // Setup control event listeners
    _setupControlListeners() {
        // Get the root element by climbing up from canvas
        const root = this.canvasRef.el?.closest('.o_sketch_widget');
        if (!root) return;

        // Clear button
        const clearBtn = root.querySelector(".o_sketch_clear");
        if (clearBtn) {
            clearBtn.setAttribute("aria-label", "Clear canvas");
            this._addEventListener(clearBtn, "click", () => this._onClear());
            this._addEventListener(clearBtn, "keydown", (ev) => {
                if (ev.key === "Enter" || ev.key === " ") {
                    ev.preventDefault();
                    this._onClear();
                }
            });
        }

        // Save button
        const saveBtn = root.querySelector(".o_sketch_save");
        if (saveBtn) {
            saveBtn.setAttribute("aria-label", "Save sketch");
            this._addEventListener(saveBtn, "click", () => this._onSave());
            this._addEventListener(saveBtn, "keydown", (ev) => {
                if (ev.key === "Enter" || ev.key === " ") {
                    ev.preventDefault();
                    this._onSave();
                }
            });
        }

        // Undo button
        const undoBtn = root.querySelector(".o_sketch_undo");
        if (undoBtn) {
            undoBtn.setAttribute("aria-label", "Undo");
            this._addEventListener(undoBtn, "click", () => this._onUndo());
            this._addEventListener(undoBtn, "keydown", (ev) => {
                if (ev.key === "Enter" || ev.key === " ") {
                    ev.preventDefault();
                    this._onUndo();
                }
            });
        }

        // Redo button
        const redoBtn = root.querySelector(".o_sketch_redo");
        if (redoBtn) {
            redoBtn.setAttribute("aria-label", "Redo");
            this._addEventListener(redoBtn, "click", () => this._onRedo());
            this._addEventListener(redoBtn, "keydown", (ev) => {
                if (ev.key === "Enter" || ev.key === " ") {
                    ev.preventDefault();
                    this._onRedo();
                }
            });
        }

        // Color input
        const colorInput = root.querySelector(".o_sketch_color");
        if (colorInput) {
            colorInput.setAttribute("aria-label", "Select drawing color");
            colorInput.value = this.currentColor;
            this._addEventListener(colorInput, "input", (ev) => {
                this.currentColor = ev.target.value;
                this._updatePreview();
            });
            this._addEventListener(colorInput, "change", (ev) => {
                this.currentColor = ev.target.value;
                this._updatePreview();
            });
        }

        // Width input (select element)
        const widthInput = root.querySelector(".o_sketch_width");
        if (widthInput) {
            widthInput.setAttribute("aria-label", "Select line width");
            widthInput.value = this.currentWidth;
            this._addEventListener(widthInput, "change", (ev) => {
                this.currentWidth = parseInt(ev.target.value, 10) || 1;
                this._updatePreview();
            });
        }

        // Quality input
        const qualityInput = root.querySelector(".o_sketch_quality");
        if (qualityInput) {
            qualityInput.setAttribute("aria-label", "Select export quality");
            qualityInput.value = this.exportQuality * 100;
            this._addEventListener(qualityInput, "change", (ev) => {
                this.exportQuality = parseInt(ev.target.value, 10) / 100;
            });
        }

        // Tool buttons
        const toolButtons = root.querySelectorAll(".o_sketch_tool");
        toolButtons.forEach(btn => {
            const tool = btn.dataset.tool || "pen";
            btn.setAttribute("aria-label", `${tool} tool`);
            this._addEventListener(btn, "click", (ev) => {
                this.currentTool = tool;
                // Update active state
                toolButtons.forEach(b => b.classList.remove("active"));
                ev.currentTarget.classList.add("active");

                // Handle measurement tool specifically
                if (tool === "measure") {
                    this.state.isMeasuring = true;
                } else {
                    this.state.isMeasuring = false;
                    this.state.showMeasurementInput = false;
                }

                this._updatePreview();
            });
            this._addEventListener(btn, "keydown", (ev) => {
                if (ev.key === "Enter" || ev.key === " ") {
                    ev.preventDefault();
                    btn.click();
                }
            });
        });

        // Measurement controls
        const measureBtn = root.querySelector('.o_sketch_tool[data-tool="measure"]');
        if (measureBtn) {
            measureBtn.setAttribute("aria-label", "Measurement tool");
        }

        // Measurement unit selector
        const unitSelect = root.querySelector(".o_measurement_unit");
        if (unitSelect) {
            unitSelect.value = this.state.measurementUnit;
            this._addEventListener(unitSelect, "change", (ev) => {
                this.state.measurementUnit = ev.target.value;
            });
        }

        // Measurement color selector
        const measureColorInput = root.querySelector(".o_measurement_color");
        if (measureColorInput) {
            measureColorInput.value = this.state.measurementColor;
            this._addEventListener(measureColorInput, "change", (ev) => {
                this.state.measurementColor = ev.target.value;
            });
        }

        // Set pen as active by default
        const penTool = root.querySelector('.o_sketch_tool[data-tool="pen"]');
        if (penTool) {
            penTool.classList.add("active");
        }

        // Initial button states
        this._updateButtonStates();
    }

    // Update preview element
    _updatePreview() {
        const preview = this.previewRef.el;
        if (preview) {
            preview.style.backgroundColor = this.currentTool === 'eraser' ? '#FFFFFF' : this.currentColor;
            preview.style.borderColor = this.currentTool === 'eraser' ? '#ccc' : this.currentColor;
            preview.style.width = `${this.currentWidth * 4}px`;
            preview.style.height = `${this.currentWidth * 4}px`;
            preview.setAttribute("aria-label", `Current tool: ${this.currentTool}, Size: ${this.currentWidth}px`);
        }
    }

    // Setup resize handling with debouncing
    _setupResizeHandling(container) {
        this._resizeObserver = new ResizeObserver(entries => {
            if (this._resizeDebounce) {
                clearTimeout(this._resizeDebounce);
            }
            this._resizeDebounce = setTimeout(() => {
                if (this._isMounted) {
                    this._syncCanvasSize(true);
                }
                this._resizeDebounce = null;
            }, 150);
        });

        if (container) {
            this._resizeObserver.observe(container);
        }
    }

    // Keyboard shortcut handler
    _onKeyDown(ev) {
        if (ev.ctrlKey || ev.metaKey) {
            switch (ev.key) {
                case 'z':
                    ev.preventDefault();
                    if (ev.shiftKey) {
                        this._onRedo();
                    } else {
                        this._onUndo();
                    }
                    break;
                case 'y':
                    ev.preventDefault();
                    this._onRedo();
                    break;
                case 's':
                    ev.preventDefault();
                    this._onSave();
                    break;
                case 'c':
                    ev.preventDefault();
                    this._onClear();
                    break;
                case 'm':
                    ev.preventDefault();
                    this._toggleMeasurementTool();
                    break;
            }
        } else if (ev.key === 'Escape') {
            if (this.state.isMeasuring && this._isMeasuring) {
                // Cancel measurement
                this._isMeasuring = false;
                this._tempMeasurementLine = null;
                this._restoreState();
            } else if (this.state.showMeasurementInput) {
                this._cancelMeasurementInput();
            }
        } else if (ev.key === 'Enter' && this.state.showMeasurementInput) {
            this._saveMeasurement();
        }
    }

    // Wheel event for measurement font size adjustment
    _onWheel(ev) {
        if (this.state.isMeasuring && ev.ctrlKey) {
            ev.preventDefault();
            const delta = Math.sign(ev.deltaY);
            this.state.measurementFontSize = Math.max(8, Math.min(72, this.state.measurementFontSize - delta));
        }
    }

    // Toggle measurement tool
    _toggleMeasurementTool() {
        const root = this.canvasRef.el?.closest('.o_sketch_widget');
        if (!root) return;

        const measureBtn = root.querySelector('.o_sketch_tool[data-tool="measure"]');
        if (measureBtn) {
            measureBtn.click();
        }
    }

    // Synchronize canvas size with container
    _syncCanvasSize(preserveContent = true) {
        const canvas = this.canvasRef.el;
        const container = this.containerRef.el;

        if (!canvas || !container || !this.ctx) return;

        const dpr = window.devicePixelRatio || 1;
        const rect = container.getBoundingClientRect();
        const cssWidth = Math.max(200, Math.floor(rect.width));
        const cssHeight = Math.max(100, Math.round(cssWidth * 0.66));

        // Check if size actually changed
        if (canvas.width === Math.round(cssWidth * dpr) &&
            canvas.height === Math.round(cssHeight * dpr)) {
            return;
        }

        // Save current content if needed
        let content = null;
        if (preserveContent && canvas.width > 0 && canvas.height > 0) {
            try {
                content = this.ctx.getImageData(0, 0, canvas.width, canvas.height);
            } catch (e) {
                console.warn("Could not get image data:", e);
            }
        }

        // Set new size
        canvas.style.width = `${cssWidth}px`;
        canvas.style.height = `${cssHeight}px`;
        canvas.width = Math.round(cssWidth * dpr);
        canvas.height = Math.round(cssHeight * dpr);

        // Reset transform for high DPI
        this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

        // Restore content if available
        if (content) {
            try {
                // Create temporary canvas to hold old content
                const tempCanvas = document.createElement('canvas');
                tempCanvas.width = content.width;
                tempCanvas.height = content.height;
                const tempCtx = tempCanvas.getContext('2d');
                tempCtx.putImageData(content, 0, 0);

                // Draw scaled content
                this.ctx.drawImage(tempCanvas, 0, 0, cssWidth, cssHeight);
            } catch (e) {
                console.warn("Could not restore content:", e);
                this._fillBackground('#FFFFFF');
            }
        } else {
            // Fill with background
            this._fillBackground('#FFFFFF');
        }
    }

    // Pointer event handlers
    _onPointerDown(ev) {
        if (ev.pointerType === "mouse" && ev.button !== 0) return;

        const canvas = this.canvasRef.el;
        if (!canvas) return;

        canvas.setPointerCapture(ev.pointerId);

        const rect = canvas.getBoundingClientRect();
        const x = (ev.clientX - rect.left) * (canvas.width / rect.width);
        const y = (ev.clientY - rect.top) * (canvas.height / rect.height);

        if (this.state.isMeasuring) {
            // Start measurement
            this._isMeasuring = true;
            this._measurementStartX = x;
            this._measurementStartY = y;
            this._measurementEndX = x;
            this._measurementEndY = y;

            // Save state before drawing temporary line
            this._saveTempState();
        } else {
            // Start drawing
            this.isDrawing = true;
            this._lastX = x;
            this._lastY = y;

            // Start drawing immediately
            this.ctx.beginPath();
            this.ctx.moveTo(x, y);
        }
    }

    _onPointerMove(ev) {
        const canvas = this.canvasRef.el;
        if (!canvas) return;

        const rect = canvas.getBoundingClientRect();
        const x = (ev.clientX - rect.left) * (canvas.width / rect.width);
        const y = (ev.clientY - rect.top) * (canvas.height / rect.height);

        if (this._isMeasuring) {
            // Update measurement line
            this._measurementEndX = x;
            this._measurementEndY = y;

            // Draw temporary measurement line
            this._drawTempMeasurementLine();
        } else if (this.isDrawing) {
            // Draw line segment
            this.ctx.lineCap = 'round';
            this.ctx.lineJoin = 'round';
            this.ctx.lineWidth = this.currentWidth;
            this.ctx.strokeStyle = this.currentTool === 'eraser' ? '#FFFFFF' : this.currentColor;

            this.ctx.beginPath();
            this.ctx.moveTo(this._lastX, this._lastY);
            this.ctx.lineTo(x, y);
            this.ctx.stroke();

            // Update last position
            this._lastX = x;
            this._lastY = y;
        }
    }

    _onPointerUp(ev) {
        const canvas = this.canvasRef.el;
        if (canvas) {
            try {
                canvas.releasePointerCapture(ev.pointerId);
            } catch (e) {
                // Ignore errors
            }
        }

        if (this._isMeasuring) {
            // Finish measurement and show input
            this._showMeasurementInput();
            this._isMeasuring = false;
        } else if (this.isDrawing) {
            this.isDrawing = false;
            this._lastX = null;
            this._lastY = null;
            this._saveState().catch(error => {
                console.warn("Failed to save state:", error);
            });
        }
    }

    // Draw temporary measurement line
    _drawTempMeasurementLine() {
        if (!this._tempMeasurementLine) return;

        // Restore to state before drawing temporary line
        this._restoreTempState();

        // Draw the measurement line
        this.ctx.beginPath();
        this.ctx.moveTo(this._measurementStartX, this._measurementStartY);
        this.ctx.lineTo(this._measurementEndX, this._measurementEndY);
        this.ctx.strokeStyle = this.state.measurementColor;
        this.ctx.lineWidth = 2;
        this.ctx.setLineDash([5, 5]);
        this.ctx.stroke();
        this.ctx.setLineDash([]);

        // Draw endpoints
        this.ctx.beginPath();
        this.ctx.arc(this._measurementStartX, this._measurementStartY, 4, 0, Math.PI * 2);
        this.ctx.arc(this._measurementEndX, this._measurementEndY, 4, 0, Math.PI * 2);
        this.ctx.fillStyle = this.state.measurementColor;
        this.ctx.fill();
    }

    // Save temporary state for measurement line
    _saveTempState() {
        const canvas = this.canvasRef.el;
        if (!canvas) return;

        try {
            this._tempMeasurementLine = this.ctx.getImageData(0, 0, canvas.width, canvas.height);
        } catch (e) {
            console.warn("Could not save temp state:", e);
        }
    }

    // Restore temporary state
    _restoreTempState() {
        if (!this._tempMeasurementLine) return;

        try {
            this.ctx.putImageData(this._tempMeasurementLine, 0, 0);
        } catch (e) {
            console.warn("Could not restore temp state:", e);
        }
    }

    // Show measurement input
    _showMeasurementInput() {
        const canvas = this.canvasRef.el;
        if (!canvas) return;

        // Calculate midpoint for measurement text
        const midX = (this._measurementStartX + this._measurementEndX) / 2;
        const midY = (this._measurementStartY + this._measurementEndY) / 2;

        // Convert to CSS coordinates
        const rect = canvas.getBoundingClientRect();
        const cssX = (midX * rect.width / canvas.width) + rect.left;
        const cssY = (midY * rect.height / canvas.height) + rect.top;

        this.state.measurementPosition = { x: cssX, y: cssY };
        this.state.showMeasurementInput = true;

        // Focus input after rendering
        setTimeout(() => {
            const input = this.measurementInputRef && this.measurementInputRef.el;
            if (input) {
                input.focus();
                input.select();
            }
        }, 10);
    }

    // Save measurement
    _saveMeasurement() {
        if (!this.state.currentMeasurement.trim()) {
            this._cancelMeasurementInput();
            return;
        }

        const canvas = this.canvasRef.el;
        if (!canvas) return;

        // Convert CSS coordinates back to canvas coordinates
        const rect = canvas.getBoundingClientRect();
        const x = (this.state.measurementPosition.x - rect.left) * (canvas.width / rect.width);
        const y = (this.state.measurementPosition.y - rect.top) * (canvas.height / rect.height);

        // Draw the final measurement line
        this.ctx.beginPath();
        this.ctx.moveTo(this._measurementStartX, this._measurementStartY);
        this.ctx.lineTo(this._measurementEndX, this._measurementEndY);
        this.ctx.strokeStyle = this.state.measurementColor;
        this.ctx.lineWidth = 2;
        this.ctx.stroke();

        // Draw endpoints
        this.ctx.beginPath();
        this.ctx.arc(this._measurementStartX, this._measurementStartY, 4, 0, Math.PI * 2);
        this.ctx.arc(this._measurementEndX, this._measurementEndY, 4, 0, Math.PI * 2);
        this.ctx.fillStyle = this.state.measurementColor;
        this.ctx.fill();

        // Draw measurement text
        this.ctx.font = `${this.state.measurementFontSize}px Arial`;
        this.ctx.fillStyle = this.state.measurementColor;
        this.ctx.textAlign = "center";
        this.ctx.textBaseline = "middle";

        const text = `${this.state.currentMeasurement} ${this.state.measurementUnit}`;
        this.ctx.fillText(text, x, y);

        // Reset state
        this.state.showMeasurementInput = false;
        this.state.currentMeasurement = "";
        this._tempMeasurementLine = null;

        // Save to history
        this._saveState().catch(error => {
            console.warn("Failed to save state:", error);
        });
    }

    // Cancel measurement input
    _cancelMeasurementInput() {
        this.state.showMeasurementInput = false;
        this.state.currentMeasurement = "";
        this._restoreState();
    }

    // Memory-efficient state saving
    async _saveState() {
        const canvas = this.canvasRef.el;
        if (!canvas) return;

        try {
            const dataUrl = canvas.toDataURL("image/png");

            // If we've undone and then drew new content, truncate "future" history
            if (this.historyIndex < this.history.length - 1) {
                this.history = this.history.slice(0, this.historyIndex + 1);
            }

            this.history.push(dataUrl);
            this.historyIndex = this.history.length - 1;

            // Enforce max history length
            while (this.history.length > this.maxHistory) {
                this.history.shift();
                this.historyIndex--;
            }

            this._updateButtonStates();
        } catch (error) {
            console.warn("SketchWidget: _saveState failed", error);
            this._showNotification("Failed to save drawing state", "warning");
        }
    }

    // Update undo/redo button states
    _updateButtonStates() {
        const root = this.canvasRef.el?.closest('.o_sketch_widget');
        if (!root) return;

        const undoBtn = root.querySelector(".o_sketch_undo");
        const redoBtn = root.querySelector(".o_sketch_redo");

        if (undoBtn) {
            undoBtn.disabled = this.historyIndex <= 0;
            undoBtn.setAttribute("aria-disabled", undoBtn.disabled);
        }
        if (redoBtn) {
            redoBtn.disabled = this.historyIndex >= this.history.length - 1;
            redoBtn.setAttribute("aria-disabled", redoBtn.disabled);
        }
    }

    // Restore state from history
    _restoreState() {
        if (this.historyIndex < 0 || this.historyIndex >= this.history.length) return;

        const canvas = this.canvasRef.el;
        if (!canvas || !this.ctx) return;

        const dataUrl = this.history[this.historyIndex];
        if (!dataUrl) return;

        const img = new Image();
        img.onload = () => {
            this.ctx.clearRect(0, 0, canvas.width, canvas.height);
            this.ctx.drawImage(img, 0, 0);
            this._updateButtonStates();
        };
        img.onerror = () => {
            console.warn("Failed to load history state");
            this._fillBackground('#FFFFFF');
        };
        img.src = dataUrl;
    }

    // Fill background
    _fillBackground(color) {
        const canvas = this.canvasRef.el;
        if (!canvas || !this.ctx) return;

        this.ctx.save();
        this.ctx.setTransform(1, 0, 0, 1, 0, 0);
        this.ctx.fillStyle = color;
        this.ctx.fillRect(0, 0, canvas.width, canvas.height);
        this.ctx.restore();
    }

    // Control actions
    _onClear() {
        if (confirm("Are you sure you want to clear the canvas?")) {
            this._fillBackground('#FFFFFF');
            this._saveState().catch(error => {
                console.warn("Failed to save after clear:", error);
            });
        }
    }

    async _onSave() {
        const canvas = this.canvasRef.el;
        if (!canvas) return;

        try {
            canvas.toBlob(async (blob) => {
                try {
                    const reader = new FileReader();
                    reader.onload = async () => {
                        const base64Data = reader.result.split(',')[1];
                        if (this.props.record) {
                            await this.props.record.update({ [this.props.name]: base64Data });
                            this._showNotification("Sketch saved successfully!", "success");
                        }
                    };
                    reader.onerror = () => {
                        throw new Error("Failed to read blob data");
                    };
                    reader.readAsDataURL(blob);
                } catch (error) {
                    console.error("Save process failed:", error);
                    this._showNotification("Failed to save sketch", "danger");
                }
            }, "image/png", this.exportQuality);
        } catch (error) {
            console.error("Save failed:", error);
            this._showNotification("Failed to save sketch", "danger");
        }
    }

    _onUndo() {
        if (this.historyIndex > 0) {
            this.historyIndex--;
            this._restoreState();
        }
    }

    _onRedo() {
        if (this.historyIndex < this.history.length - 1) {
            this.historyIndex++;
            this._restoreState();
        }
    }

    // Show notification using Odoo's notification service
    _showNotification(message, type = "info") {
        this.notification.add(message, {
            type: type,
            title: type.charAt(0).toUpperCase() + type.slice(1),
        });
    }

    // Cleanup
    _cleanup() {
        this._isMounted = false;

        // Remove all event listeners
        this._eventListeners.forEach(({ element, event, handler, options }) => {
            if (element) {
                element.removeEventListener(event, handler, options);
            }
        });
        this._eventListeners = [];

        // Cleanup resize observer
        if (this._resizeObserver) {
            this._resizeObserver.disconnect();
            this._resizeObserver = null;
        }

        if (this._resizeDebounce) {
            clearTimeout(this._resizeDebounce);
            this._resizeDebounce = null;
        }

        // Cleanup history
        this.history = [];
        this.historyIndex = -1;
    }
}

CommissionSketchWidget.template = "CommissionSketchWidget";
CommissionSketchWidget.props = {
    record: Object,
    name: String,
};

registry.category("fields").add("commission_sketch", {
    component: CommissionSketchWidget,
});*/

/** @odoo-module **/
/*
import { registry } from "@web/core/registry";
import { Component, useRef, onMounted, onWillUnmount, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class CommissionSketchWidget extends Component {
    setup() {
        // Services
        this.notification = useService("notification");

        // Refs
        this.canvasRef = useRef("canvas");
        this.containerRef = useRef("container");
        this.previewRef = useRef("preview");

        // State management
        this.state = useState({
            isMeasuring: false,
            measurementUnit: "cm",
            measurementFontSize: 16,
            measurementColor: "#0000FF",
            measurements: [] // Store all measurements {startX, startY, endX, endY, value, unit}
        });

        // Drawing state
        this.ctx = null;
        this.isDrawing = false;
        this.currentColor = "#000000";
        this.currentWidth = 3;
        this.currentTool = "pen";
        this.exportQuality = 0.92;

        // History config
        this.maxHistory = 50;
        this.history = [];
        this.historyIndex = -1;

        // Drawing state
        this._lastX = null;
        this._lastY = null;

        // Measurement state
        this._measurementStartX = null;
        this._measurementStartY = null;
        this._measurementEndX = null;
        this._measurementEndY = null;
        this._isMeasuring = false;
        this._tempMeasurementLine = null;

        // High DPI configuration
        this.dpr = window.devicePixelRatio || 1;

        // Flags
        this._isMounted = false;

        // Touch device detection
        this.isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;

        // Store event listeners for proper cleanup
        this._eventListeners = [];

        // Bind handlers
        this._onPointerDown = this._onPointerDown.bind(this);
        this._onPointerMove = this._onPointerMove.bind(this);
        this._onPointerUp = this._onPointerUp.bind(this);
        this._onPointerCancel = this._onPointerUp.bind(this);
        this._onKeyDown = this._onKeyDown.bind(this);
        this._onWheel = this._onWheel.bind(this);

        onMounted(() => this._init());
        onWillUnmount(() => this._cleanup());
    }

    // Initialize canvas and listeners
    async _init() {
        this._isMounted = true;
        const canvas = this.canvasRef.el;
        const container = this.containerRef.el;

        if (!canvas || !container) {
            console.warn("SketchWidget: canvas or container missing");
            return;
        }

        this.ctx = canvas.getContext("2d", { willReadFrequently: true });

        // Setup dimensions, high-DPI scaling
        this._syncCanvasSize();

        // Initialize white background and save initial state
        this._fillBackground('#FFFFFF');
        await this._saveState();

        // Pointer events
        canvas.style.touchAction = "none";
        this._addEventListener(canvas, "pointerdown", this._onPointerDown);
        this._addEventListener(canvas, "pointermove", this._onPointerMove);
        this._addEventListener(canvas, "pointerup", this._onPointerUp);
        this._addEventListener(canvas, "pointercancel", this._onPointerCancel);

        // Wheel for measurement font size adjustment
        this._addEventListener(canvas, "wheel", this._onWheel, { passive: false });

        // Keyboard shortcuts
        this._addEventListener(window, "keydown", this._onKeyDown);

        // Setup control event listeners
        this._setupControlListeners();

        // Setup resize handling
        this._setupResizeHandling(container);

        // Update preview
        this._updatePreview();

        // Set initial focus for accessibility
        canvas.setAttribute("tabindex", "0");
        canvas.setAttribute("aria-label", "Drawing canvas");
        canvas.focus();
    }

    // Helper to add and track event listeners
    _addEventListener(element, event, handler, options) {
        if (element) {
            element.addEventListener(event, handler, options);
            this._eventListeners.push({ element, event, handler, options });
        }
    }

    // Setup control event listeners
    _setupControlListeners() {
        // Get the root element by climbing up from canvas
        const root = this.canvasRef.el?.closest('.o_sketch_widget');
        if (!root) return;

        // Clear button
        const clearBtn = root.querySelector(".o_sketch_clear");
        if (clearBtn) {
            clearBtn.setAttribute("aria-label", "Clear canvas");
            this._addEventListener(clearBtn, "click", () => this._onClear());
            this._addEventListener(clearBtn, "keydown", (ev) => {
                if (ev.key === "Enter" || ev.key === " ") {
                    ev.preventDefault();
                    this._onClear();
                }
            });
        }

        // Save button
        const saveBtn = root.querySelector(".o_sketch_save");
        if (saveBtn) {
            saveBtn.setAttribute("aria-label", "Save sketch");
            this._addEventListener(saveBtn, "click", () => this._onSave());
            this._addEventListener(saveBtn, "keydown", (ev) => {
                if (ev.key === "Enter" || ev.key === " ") {
                    ev.preventDefault();
                    this._onSave();
                }
            });
        }

        // Undo button
        const undoBtn = root.querySelector(".o_sketch_undo");
        if (undoBtn) {
            undoBtn.setAttribute("aria-label", "Undo");
            this._addEventListener(undoBtn, "click", () => this._onUndo());
            this._addEventListener(undoBtn, "keydown", (ev) => {
                if (ev.key === "Enter" || ev.key === " ") {
                    ev.preventDefault();
                    this._onUndo();
                }
            });
        }

        // Redo button
        const redoBtn = root.querySelector(".o_sketch_redo");
        if (redoBtn) {
            redoBtn.setAttribute("aria-label", "Redo");
            this._addEventListener(redoBtn, "click", () => this._onRedo());
            this._addEventListener(redoBtn, "keydown", (ev) => {
                if (ev.key === "Enter" || ev.key === " ") {
                    ev.preventDefault();
                    this._onRedo();
                }
            });
        }

        // Color input
        const colorInput = root.querySelector(".o_sketch_color");
        if (colorInput) {
            colorInput.setAttribute("aria-label", "Select drawing color");
            colorInput.value = this.currentColor;
            this._addEventListener(colorInput, "input", (ev) => {
                this.currentColor = ev.target.value;
                this._updatePreview();
            });
            this._addEventListener(colorInput, "change", (ev) => {
                this.currentColor = ev.target.value;
                this._updatePreview();
            });
        }

        // Width input (select element)
        const widthInput = root.querySelector(".o_sketch_width");
        if (widthInput) {
            widthInput.setAttribute("aria-label", "Select line width");
            widthInput.value = this.currentWidth;
            this._addEventListener(widthInput, "change", (ev) => {
                this.currentWidth = parseInt(ev.target.value, 10) || 1;
                this._updatePreview();
            });
        }

        // Quality input
        const qualityInput = root.querySelector(".o_sketch_quality");
        if (qualityInput) {
            qualityInput.setAttribute("aria-label", "Select export quality");
            qualityInput.value = this.exportQuality * 100;
            this._addEventListener(qualityInput, "change", (ev) => {
                this.exportQuality = parseInt(ev.target.value, 10) / 100;
            });
        }

        // Tool buttons
        const toolButtons = root.querySelectorAll(".o_sketch_tool");
        toolButtons.forEach(btn => {
            const tool = btn.dataset.tool || "pen";
            btn.setAttribute("aria-label", `${tool} tool`);
            this._addEventListener(btn, "click", (ev) => {
                this.currentTool = tool;
                // Update active state
                toolButtons.forEach(b => b.classList.remove("active"));
                ev.currentTarget.classList.add("active");

                // Handle measurement tool specifically
                if (tool === "measure") {
                    this.state.isMeasuring = true;
                } else {
                    this.state.isMeasuring = false;
                }

                this._updatePreview();
            });
            this._addEventListener(btn, "keydown", (ev) => {
                if (ev.key === "Enter" || ev.key === " ") {
                    ev.preventDefault();
                    btn.click();
                }
            });
        });

        // Measurement controls
        const measureBtn = root.querySelector('.o_sketch_tool[data-tool="measure"]');
        if (measureBtn) {
            measureBtn.setAttribute("aria-label", "Measurement tool");
        }

        // Measurement unit selector
        const unitSelect = root.querySelector(".o_measurement_unit");
        if (unitSelect) {
            unitSelect.value = this.state.measurementUnit;
            this._addEventListener(unitSelect, "change", (ev) => {
                this.state.measurementUnit = ev.target.value;
            });
        }

        // Measurement color selector
        const measureColorInput = root.querySelector(".o_measurement_color");
        if (measureColorInput) {
            measureColorInput.value = this.state.measurementColor;
            this._addEventListener(measureColorInput, "change", (ev) => {
                this.state.measurementColor = ev.target.value;
            });
        }

        // Set pen as active by default
        const penTool = root.querySelector('.o_sketch_tool[data-tool="pen"]');
        if (penTool) {
            penTool.classList.add("active");
        }

        // Initial button states
        this._updateButtonStates();
    }

    // Update preview element
    _updatePreview() {
        const preview = this.previewRef.el;
        if (preview) {
            preview.style.backgroundColor = this.currentTool === 'eraser' ? '#FFFFFF' : this.currentColor;
            preview.style.borderColor = this.currentTool === 'eraser' ? '#ccc' : this.currentColor;
            preview.style.width = `${this.currentWidth * 4}px`;
            preview.style.height = `${this.currentWidth * 4}px`;
            preview.setAttribute("aria-label", `Current tool: ${this.currentTool}, Size: ${this.currentWidth}px`);
        }
    }

    // Setup resize handling with debouncing
    _setupResizeHandling(container) {
        this._resizeObserver = new ResizeObserver(entries => {
            if (this._resizeDebounce) {
                clearTimeout(this._resizeDebounce);
            }
            this._resizeDebounce = setTimeout(() => {
                if (this._isMounted) {
                    this._syncCanvasSize(true);
                }
                this._resizeDebounce = null;
            }, 150);
        });

        if (container) {
            this._resizeObserver.observe(container);
        }
    }

    // Keyboard shortcut handler
    _onKeyDown(ev) {
        if (ev.ctrlKey || ev.metaKey) {
            switch (ev.key) {
                case 'z':
                    ev.preventDefault();
                    if (ev.shiftKey) {
                        this._onRedo();
                    } else {
                        this._onUndo();
                    }
                    break;
                case 'y':
                    ev.preventDefault();
                    this._onRedo();
                    break;
                case 's':
                    ev.preventDefault();
                    this._onSave();
                    break;
                case 'c':
                    ev.preventDefault();
                    this._onClear();
                    break;
                case 'm':
                    ev.preventDefault();
                    this._toggleMeasurementTool();
                    break;
            }
        } else if (ev.key === 'Escape') {
            if (this.state.isMeasuring && this._isMeasuring) {
                // Cancel measurement
                this._isMeasuring = false;
                this._tempMeasurementLine = null;
                this._restoreState();
            }
        }
    }

    // Wheel event for measurement font size adjustment
    _onWheel(ev) {
        if (this.state.isMeasuring && ev.ctrlKey) {
            ev.preventDefault();
            const delta = Math.sign(ev.deltaY);
            this.state.measurementFontSize = Math.max(8, Math.min(72, this.state.measurementFontSize - delta));
        }
    }

    // Toggle measurement tool
    _toggleMeasurementTool() {
        const root = this.canvasRef.el?.closest('.o_sketch_widget');
        if (!root) return;

        const measureBtn = root.querySelector('.o_sketch_tool[data-tool="measure"]');
        if (measureBtn) {
            measureBtn.click();
        }
    }

    // Synchronize canvas size with container
    _syncCanvasSize(preserveContent = true) {
        const canvas = this.canvasRef.el;
        const container = this.containerRef.el;

        if (!canvas || !container || !this.ctx) return;

        const dpr = window.devicePixelRatio || 1;
        const rect = container.getBoundingClientRect();
        const cssWidth = Math.max(200, Math.floor(rect.width));
        const cssHeight = Math.max(100, Math.round(cssWidth * 0.66));

        // Check if size actually changed
        if (canvas.width === Math.round(cssWidth * dpr) &&
            canvas.height === Math.round(cssHeight * dpr)) {
            return;
        }

        // Save current content if needed
        let content = null;
        if (preserveContent && canvas.width > 0 && canvas.height > 0) {
            try {
                content = this.ctx.getImageData(0, 0, canvas.width, canvas.height);
            } catch (e) {
                console.warn("Could not get image data:", e);
            }
        }

        // Set new size
        canvas.style.width = `${cssWidth}px`;
        canvas.style.height = `${cssHeight}px`;
        canvas.width = Math.round(cssWidth * dpr);
        canvas.height = Math.round(cssHeight * dpr);

        // Reset transform for high DPI
        this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

        // Restore content if available
        if (content) {
            try {
                // Create temporary canvas to hold old content
                const tempCanvas = document.createElement('canvas');
                tempCanvas.width = content.width;
                tempCanvas.height = content.height;
                const tempCtx = tempCanvas.getContext('2d');
                tempCtx.putImageData(content, 0, 0);

                // Draw scaled content
                this.ctx.drawImage(tempCanvas, 0, 0, cssWidth, cssHeight);
            } catch (e) {
                console.warn("Could not restore content:", e);
                this._fillBackground('#FFFFFF');
            }
        } else {
            // Fill with background
            this._fillBackground('#FFFFFF');
        }
    }

    // Pointer event handlers
    _onPointerDown(ev) {
        if (ev.pointerType === "mouse" && ev.button !== 0) return;

        const canvas = this.canvasRef.el;
        if (!canvas) return;

        canvas.setPointerCapture(ev.pointerId);

        const rect = canvas.getBoundingClientRect();
        const x = (ev.clientX - rect.left) * (canvas.width / rect.width);
        const y = (ev.clientY - rect.top) * (canvas.height / rect.height);

        if (this.state.isMeasuring) {
            // Start measurement
            this._isMeasuring = true;
            this._measurementStartX = x;
            this._measurementStartY = y;
            this._measurementEndX = x;
            this._measurementEndY = y;

            // Save state before drawing temporary line
            this._saveTempState();
        } else {
            // Start drawing
            this.isDrawing = true;
            this._lastX = x;
            this._lastY = y;

            // Start drawing immediately
            this.ctx.beginPath();
            this.ctx.moveTo(x, y);
        }
    }

    _onPointerMove(ev) {
        const canvas = this.canvasRef.el;
        if (!canvas) return;

        const rect = canvas.getBoundingClientRect();
        const x = (ev.clientX - rect.left) * (canvas.width / rect.width);
        const y = (ev.clientY - rect.top) * (canvas.height / rect.height);

        if (this._isMeasuring) {
            // Update measurement line
            this._measurementEndX = x;
            this._measurementEndY = y;

            // Draw temporary measurement line
            this._drawTempMeasurementLine();
        } else if (this.isDrawing) {
            // Draw line segment
            this.ctx.lineCap = 'round';
            this.ctx.lineJoin = 'round';
            this.ctx.lineWidth = this.currentWidth;
            this.ctx.strokeStyle = this.currentTool === 'eraser' ? '#FFFFFF' : this.currentColor;

            this.ctx.beginPath();
            this.ctx.moveTo(this._lastX, this._lastY);
            this.ctx.lineTo(x, y);
            this.ctx.stroke();

            // Update last position
            this._lastX = x;
            this._lastY = y;
        }
    }

    _onPointerUp(ev) {
        const canvas = this.canvasRef.el;
        if (canvas) {
            try {
                canvas.releasePointerCapture(ev.pointerId);
            } catch (e) {
                // Ignore errors
            }
        }

        if (this._isMeasuring) {
            // Finish measurement and calculate value
            this._saveMeasurement();
            this._isMeasuring = false;
        } else if (this.isDrawing) {
            this.isDrawing = false;
            this._lastX = null;
            this._lastY = null;
            this._saveState().catch(error => {
                console.warn("Failed to save state:", error);
            });
        }
    }

    // Draw temporary measurement line
    _drawTempMeasurementLine() {
        if (!this._tempMeasurementLine) return;

        // Restore to state before drawing temporary line
        this._restoreTempState();

        // Draw the measurement line
        this.ctx.beginPath();
        this.ctx.moveTo(this._measurementStartX, this._measurementStartY);
        this.ctx.lineTo(this._measurementEndX, this._measurementEndY);
        this.ctx.strokeStyle = this.state.measurementColor;
        this.ctx.lineWidth = 2;
        this.ctx.setLineDash([5, 5]);
        this.ctx.stroke();
        this.ctx.setLineDash([]);

        // Draw endpoints
        this.ctx.beginPath();
        this.ctx.arc(this._measurementStartX, this._measurementStartY, 4, 0, Math.PI * 2);
        this.ctx.arc(this._measurementEndX, this._measurementEndY, 4, 0, Math.PI * 2);
        this.ctx.fillStyle = this.state.measurementColor;
        this.ctx.fill();

        // Draw measurement value
        this._drawMeasurementValue(this._measurementStartX, this._measurementStartY,
                                 this._measurementEndX, this._measurementEndY, true);
    }

    // Draw measurement value
    _drawMeasurementValue(startX, startY, endX, endY, isTemporary = false) {
        // Calculate distance in pixels
        const dx = endX - startX;
        const dy = endY - startY;
        const distance = Math.sqrt(dx * dx + dy * dy);

        // Convert to selected unit (pixels to cm approximation)
        let measurementValue;
        switch(this.state.measurementUnit) {
            case "mm":
                measurementValue = (distance / 3.78).toFixed(1); // Approximation
                break;
            case "cm":
                measurementValue = (distance / 37.8).toFixed(1); // Approximation
                break;
            case "m":
                measurementValue = (distance / 3780).toFixed(2); // Approximation
                break;
            case "in":
                measurementValue = (distance / 96).toFixed(1); // Approximation
                break;
            case "ft":
                measurementValue = (distance / 1152).toFixed(1); // Approximation
                break;
            default:
                measurementValue = distance.toFixed(0);
        }

        // Calculate midpoint for text
        const midX = (startX + endX) / 2;
        const midY = (startY + endY) / 2;

        // Draw measurement text
        this.ctx.font = `${this.state.measurementFontSize}px Arial`;
        this.ctx.fillStyle = isTemporary ? '#888' : this.state.measurementColor;
        this.ctx.textAlign = "center";
        this.ctx.textBaseline = "middle";

        const text = `${measurementValue} ${this.state.measurementUnit}`;
        this.ctx.fillText(text, midX, midY);

        return measurementValue;
    }

    // Save temporary state for measurement line
    _saveTempState() {
        const canvas = this.canvasRef.el;
        if (!canvas) return;

        try {
            this._tempMeasurementLine = this.ctx.getImageData(0, 0, canvas.width, canvas.height);
        } catch (e) {
            console.warn("Could not save temp state:", e);
        }
    }

    // Restore temporary state
    _restoreTempState() {
        if (!this._tempMeasurementLine) return;

        try {
            this.ctx.putImageData(this._tempMeasurementLine, 0, 0);
        } catch (e) {
            console.warn("Could not restore temp state:", e);
        }
    }

    // Save measurement
    _saveMeasurement() {
        const canvas = this.canvasRef.el;
        if (!canvas) return;

        // Draw the final measurement line
        this.ctx.beginPath();
        this.ctx.moveTo(this._measurementStartX, this._measurementStartY);
        this.ctx.lineTo(this._measurementEndX, this._measurementEndY);
        this.ctx.strokeStyle = this.state.measurementColor;
        this.ctx.lineWidth = 2;
        this.ctx.stroke();

        // Draw endpoints
        this.ctx.beginPath();
        this.ctx.arc(this._measurementStartX, this._measurementStartY, 4, 0, Math.PI * 2);
        this.ctx.arc(this._measurementEndX, this._measurementEndY, 4, 0, Math.PI * 2);
        this.ctx.fillStyle = this.state.measurementColor;
        this.ctx.fill();

        // Draw measurement value
        const measurementValue = this._drawMeasurementValue(
            this._measurementStartX, this._measurementStartY,
            this._measurementEndX, this._measurementEndY
        );

        // Store measurement
        this.state.measurements.push({
            startX: this._measurementStartX,
            startY: this._measurementStartY,
            endX: this._measurementEndX,
            endY: this._measurementEndY,
            value: measurementValue,
            unit: this.state.measurementUnit
        });

        // Reset state
        this._tempMeasurementLine = null;

        // Save to history
        this._saveState().catch(error => {
            console.warn("Failed to save state:", error);
        });
    }

    // Memory-efficient state saving
    async _saveState() {
        const canvas = this.canvasRef.el;
        if (!canvas) return;

        try {
            const dataUrl = canvas.toDataURL("image/png");

            // If we've undone and then drew new content, truncate "future" history
            if (this.historyIndex < this.history.length - 1) {
                this.history = this.history.slice(0, this.historyIndex + 1);
            }

            this.history.push(dataUrl);
            this.historyIndex = this.history.length - 1;

            // Enforce max history length
            while (this.history.length > this.maxHistory) {
                this.history.shift();
                this.historyIndex--;
            }

            this._updateButtonStates();
        } catch (error) {
            console.warn("SketchWidget: _saveState failed", error);
            this._showNotification("Failed to save drawing state", "warning");
        }
    }

    // Update undo/redo button states
    _updateButtonStates() {
        const root = this.canvasRef.el?.closest('.o_sketch_widget');
        if (!root) return;

        const undoBtn = root.querySelector(".o_sketch_undo");
        const redoBtn = root.querySelector(".o_sketch_redo");

        if (undoBtn) {
            undoBtn.disabled = this.historyIndex <= 0;
            undoBtn.setAttribute("aria-disabled", undoBtn.disabled);
        }
        if (redoBtn) {
            redoBtn.disabled = this.historyIndex >= this.history.length - 1;
            redoBtn.setAttribute("aria-disabled", redoBtn.disabled);
        }
    }

    // Restore state from history
    _restoreState() {
        if (this.historyIndex < 0 || this.historyIndex >= this.history.length) return;

        const canvas = this.canvasRef.el;
        if (!canvas || !this.ctx) return;

        const dataUrl = this.history[this.historyIndex];
        if (!dataUrl) return;

        const img = new Image();
        img.onload = () => {
            this.ctx.clearRect(0, 0, canvas.width, canvas.height);
            this.ctx.drawImage(img, 0, 0);
            this._updateButtonStates();
        };
        img.onerror = () => {
            console.warn("Failed to load history state");
            this._fillBackground('#FFFFFF');
        };
        img.src = dataUrl;
    }

    // Fill background
    _fillBackground(color) {
        const canvas = this.canvasRef.el;
        if (!canvas || !this.ctx) return;

        this.ctx.save();
        this.ctx.setTransform(1, 0, 0, 1, 0, 0);
        this.ctx.fillStyle = color;
        this.ctx.fillRect(0, 0, canvas.width, canvas.height);
        this.ctx.restore();

        // Clear measurements
        this.state.measurements = [];
    }

    // Control actions
    _onClear() {
        if (confirm("Are you sure you want to clear the canvas?")) {
            this._fillBackground('#FFFFFF');
            this._saveState().catch(error => {
                console.warn("Failed to save after clear:", error);
            });
        }
    }

    async _onSave() {
        const canvas = this.canvasRef.el;
        if (!canvas) return;

        try {
            canvas.toBlob(async (blob) => {
                try {
                    const reader = new FileReader();
                    reader.onload = async () => {
                        const base64Data = reader.result.split(',')[1];
                        if (this.props.record) {
                            await this.props.record.update({ [this.props.name]: base64Data });
                            this._showNotification("Sketch saved successfully!", "success");
                        }
                    };
                    reader.onerror = () => {
                        throw new Error("Failed to read blob data");
                    };
                    reader.readAsDataURL(blob);
                } catch (error) {
                    console.error("Save process failed:", error);
                    this._showNotification("Failed to save sketch", "danger");
                }
            }, "image/png", this.exportQuality);
        } catch (error) {
            console.error("Save failed:", error);
            this._showNotification("Failed to save sketch", "danger");
        }
    }

    _onUndo() {
        if (this.historyIndex > 0) {
            this.historyIndex--;
            this._restoreState();
        }
    }

    _onRedo() {
        if (this.historyIndex < this.history.length - 1) {
            this.historyIndex++;
            this._restoreState();
        }
    }

    // Show notification using Odoo's notification service
    _showNotification(message, type = "info") {
        this.notification.add(message, {
            type: type,
            title: type.charAt(0).toUpperCase() + type.slice(1),
        });
    }

    // Cleanup
    _cleanup() {
        this._isMounted = false;

        // Remove all event listeners
        this._eventListeners.forEach(({ element, event, handler, options }) => {
            if (element) {
                element.removeEventListener(event, handler, options);
            }
        });
        this._eventListeners = [];

        // Cleanup resize observer
        if (this._resizeObserver) {
            this._resizeObserver.disconnect();
            this._resizeObserver = null;
        }

        if (this._resizeDebounce) {
            clearTimeout(this._resizeDebounce);
            this._resizeDebounce = null;
        }

        // Cleanup history
        this.history = [];
        this.historyIndex = -1;
    }
}

CommissionSketchWidget.template = "CommissionSketchWidget";
CommissionSketchWidget.props = {
    record: Object,
    name: String,
};

registry.category("fields").add("commission_sketch", {
    component: CommissionSketchWidget,
});*/

/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useRef, onMounted, onWillUnmount, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class CommissionSketchWidget extends Component {
    setup() {
        // Services
        this.notification = useService("notification");

        // Refs
        this.canvasRef = useRef("canvas");
        this.containerRef = useRef("container");
        this.previewRef = useRef("preview");
        this.measurementInputRef = useRef("measurementInput");

        // State management
        this.state = useState({
            isMeasuring: false,
            measurementUnit: "cm",
            measurementFontSize: 16,
            measurementColor: "#0000FF",
            measurements: [], // Store all measurements {id, startX, startY, endX, endY, value, unit}
            editingMeasurement: null, // Currently edited measurement
            showMeasurementInput: false,
            measurementPosition: { x: 0, y: 0 }
        });

        // Drawing state
        this.ctx = null;
        this.isDrawing = false;
        this.currentColor = "#000000";
        this.currentWidth = 3;
        this.currentTool = "pen";
        this.exportQuality = 0.92;

        // History config
        this.maxHistory = 50;
        this.history = [];
        this.historyIndex = -1;

        // Drawing state
        this._lastX = null;
        this._lastY = null;

        // Measurement state
        this._measurementStartX = null;
        this._measurementStartY = null;
        this._measurementEndX = null;
        this._measurementEndY = null;
        this._isMeasuring = false;
        this._tempMeasurementLine = null;
        this._selectedMeasurement = null;

        // High DPI configuration
        this.dpr = window.devicePixelRatio || 1;

        // Flags
        this._isMounted = false;

        // Touch device detection
        this.isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;

        // Store event listeners for proper cleanup
        this._eventListeners = [];

        // Bind handlers
        this._onPointerDown = this._onPointerDown.bind(this);
        this._onPointerMove = this._onPointerMove.bind(this);
        this._onPointerUp = this._onPointerUp.bind(this);
        this._onPointerCancel = this._onPointerUp.bind(this);
        this._onKeyDown = this._onKeyDown.bind(this);
        this._onWheel = this._onWheel.bind(this);
        this._onCanvasClick = this._onCanvasClick.bind(this);

        onMounted(() => this._init());
        onWillUnmount(() => this._cleanup());
    }

    // Initialize canvas and listeners
    async _init() {
        this._isMounted = true;
        const canvas = this.canvasRef.el;
        const container = this.containerRef.el;

        if (!canvas || !container) {
            console.warn("SketchWidget: canvas or container missing");
            return;
        }

        this.ctx = canvas.getContext("2d", { willReadFrequently: true });

        // Setup dimensions, high-DPI scaling
        this._syncCanvasSize();

        // Initialize white background and save initial state
        this._fillBackground('#FFFFFF');
        await this._saveState();

        // Pointer events
        canvas.style.touchAction = "none";
        this._addEventListener(canvas, "pointerdown", this._onPointerDown);
        this._addEventListener(canvas, "pointermove", this._onPointerMove);
        this._addEventListener(canvas, "pointerup", this._onPointerUp);
        this._addEventListener(canvas, "pointercancel", this._onPointerCancel);
        this._addEventListener(canvas, "click", this._onCanvasClick);

        // Wheel for measurement font size adjustment
        this._addEventListener(canvas, "wheel", this._onWheel, { passive: false });

        // Keyboard shortcuts
        this._addEventListener(window, "keydown", this._onKeyDown);

        // Setup control event listeners
        this._setupControlListeners();

        // Setup resize handling
        this._setupResizeHandling(container);

        // Update preview
        this._updatePreview();

        // Set initial focus for accessibility
        canvas.setAttribute("tabindex", "0");
        canvas.setAttribute("aria-label", "Drawing canvas");
        canvas.focus();
    }

    // Helper to add and track event listeners
    _addEventListener(element, event, handler, options) {
        if (element) {
            element.addEventListener(event, handler, options);
            this._eventListeners.push({ element, event, handler, options });
        }
    }

    // Setup control event listeners
    _setupControlListeners() {
        // Get the root element by climbing up from canvas
        const root = this.canvasRef.el?.closest('.o_sketch_widget');
        if (!root) return;

        // Clear button
        const clearBtn = root.querySelector(".o_sketch_clear");
        if (clearBtn) {
            clearBtn.setAttribute("aria-label", "Clear canvas");
            this._addEventListener(clearBtn, "click", () => this._onClear());
            this._addEventListener(clearBtn, "keydown", (ev) => {
                if (ev.key === "Enter" || ev.key === " ") {
                    ev.preventDefault();
                    this._onClear();
                }
            });
        }

        // Save button
        const saveBtn = root.querySelector(".o_sketch_save");
        if (saveBtn) {
            saveBtn.setAttribute("aria-label", "Save sketch");
            this._addEventListener(saveBtn, "click", () => this._onSave());
            this._addEventListener(saveBtn, "keydown", (ev) => {
                if (ev.key === "Enter" || ev.key === " ") {
                    ev.preventDefault();
                    this._onSave();
                }
            });
        }

        // Undo button
        const undoBtn = root.querySelector(".o_sketch_undo");
        if (undoBtn) {
            undoBtn.setAttribute("aria-label", "Undo");
            this._addEventListener(undoBtn, "click", () => this._onUndo());
            this._addEventListener(undoBtn, "keydown", (ev) => {
                if (ev.key === "Enter" || ev.key === " ") {
                    ev.preventDefault();
                    this._onUndo();
                }
            });
        }

        // Redo button
        const redoBtn = root.querySelector(".o_sketch_redo");
        if (redoBtn) {
            redoBtn.setAttribute("aria-label", "Redo");
            this._addEventListener(redoBtn, "click", () => this._onRedo());
            this._addEventListener(redoBtn, "keydown", (ev) => {
                if (ev.key === "Enter" || ev.key === " ") {
                    ev.preventDefault();
                    this._onRedo();
                }
            });
        }

        // Color input
        const colorInput = root.querySelector(".o_sketch_color");
        if (colorInput) {
            colorInput.setAttribute("aria-label", "Select drawing color");
            colorInput.value = this.currentColor;
            this._addEventListener(colorInput, "input", (ev) => {
                this.currentColor = ev.target.value;
                this._updatePreview();
            });
            this._addEventListener(colorInput, "change", (ev) => {
                this.currentColor = ev.target.value;
                this._updatePreview();
            });
        }

        // Width input (select element)
        const widthInput = root.querySelector(".o_sketch_width");
        if (widthInput) {
            widthInput.setAttribute("aria-label", "Select line width");
            widthInput.value = this.currentWidth;
            this._addEventListener(widthInput, "change", (ev) => {
                this.currentWidth = parseInt(ev.target.value, 10) || 1;
                this._updatePreview();
            });
        }

        // Quality input
        const qualityInput = root.querySelector(".o_sketch_quality");
        if (qualityInput) {
            qualityInput.setAttribute("aria-label", "Select export quality");
            qualityInput.value = this.exportQuality * 100;
            this._addEventListener(qualityInput, "change", (ev) => {
                this.exportQuality = parseInt(ev.target.value, 10) / 100;
            });
        }

        // Tool buttons
        const toolButtons = root.querySelectorAll(".o_sketch_tool");
        toolButtons.forEach(btn => {
            const tool = btn.dataset.tool || "pen";
            btn.setAttribute("aria-label", `${tool} tool`);
            this._addEventListener(btn, "click", (ev) => {
                this.currentTool = tool;
                // Update active state
                toolButtons.forEach(b => b.classList.remove("active"));
                ev.currentTarget.classList.add("active");

                // Handle measurement tool specifically
                if (tool === "measure") {
                    this.state.isMeasuring = true;
                } else {
                    this.state.isMeasuring = false;
                    this.state.showMeasurementInput = false;
                }

                this._updatePreview();
            });
            this._addEventListener(btn, "keydown", (ev) => {
                if (ev.key === "Enter" || ev.key === " ") {
                    ev.preventDefault();
                    btn.click();
                }
            });
        });

        // Measurement controls
        const measureBtn = root.querySelector('.o_sketch_tool[data-tool="measure"]');
        if (measureBtn) {
            measureBtn.setAttribute("aria-label", "Measurement tool");
        }

        // Measurement unit selector
        const unitSelect = root.querySelector(".o_measurement_unit");
        if (unitSelect) {
            unitSelect.value = this.state.measurementUnit;
            this._addEventListener(unitSelect, "change", (ev) => {
                this.state.measurementUnit = ev.target.value;
                // Update all measurements with new unit
                this.state.measurements.forEach(measurement => {
                    measurement.unit = this.state.measurementUnit;
                });
                this._redrawCanvas();
            });
        }

        // Measurement color selector
        const measureColorInput = root.querySelector(".o_measurement_color");
        if (measureColorInput) {
            measureColorInput.value = this.state.measurementColor;
            this._addEventListener(measureColorInput, "change", (ev) => {
                this.state.measurementColor = ev.target.value;
                this._redrawCanvas();
            });
        }

        // Measurement input handler
        const measurementInput = root.querySelector(".o_measurement_input");
        if (measurementInput) {
            this._addEventListener(measurementInput, "keydown", (ev) => {
                if (ev.key === 'Enter') {
                    this._saveMeasurementEdit();
                } else if (ev.key === 'Escape') {
                    this._cancelMeasurementEdit();
                }
            });
        }

        // Set pen as active by default
        const penTool = root.querySelector('.o_sketch_tool[data-tool="pen"]');
        if (penTool) {
            penTool.classList.add("active");
        }

        // Initial button states
        this._updateButtonStates();
    }

    // Update preview element
    _updatePreview() {
        const preview = this.previewRef.el;
        if (preview) {
            preview.style.backgroundColor = this.currentTool === 'eraser' ? '#FFFFFF' : this.currentColor;
            preview.style.borderColor = this.currentTool === 'eraser' ? '#ccc' : this.currentColor;
            preview.style.width = `${this.currentWidth * 4}px`;
            preview.style.height = `${this.currentWidth * 4}px`;
            preview.setAttribute("aria-label", `Current tool: ${this.currentTool}, Size: ${this.currentWidth}px`);
        }
    }

    // Setup resize handling with debouncing
    _setupResizeHandling(container) {
        this._resizeObserver = new ResizeObserver(entries => {
            if (this._resizeDebounce) {
                clearTimeout(this._resizeDebounce);
            }
            this._resizeDebounce = setTimeout(() => {
                if (this._isMounted) {
                    this._syncCanvasSize(true);
                }
                this._resizeDebounce = null;
            }, 150);
        });

        if (container) {
            this._resizeObserver.observe(container);
        }
    }

    // Keyboard shortcut handler
    _onKeyDown(ev) {
        if (ev.ctrlKey || ev.metaKey) {
            switch (ev.key) {
                case 'z':
                    ev.preventDefault();
                    if (ev.shiftKey) {
                        this._onRedo();
                    } else {
                        this._onUndo();
                    }
                    break;
                case 'y':
                    ev.preventDefault();
                    this._onRedo();
                    break;
                case 's':
                    ev.preventDefault();
                    this._onSave();
                    break;
                case 'c':
                    ev.preventDefault();
                    this._onClear();
                    break;
                case 'm':
                    ev.preventDefault();
                    this._toggleMeasurementTool();
                    break;
            }
        } else if (ev.key === 'Escape') {
            if (this.state.isMeasuring && this._isMeasuring) {
                // Cancel measurement
                this._isMeasuring = false;
                this._tempMeasurementLine = null;
                this._restoreState();
            } else if (this.state.showMeasurementInput) {
                this._cancelMeasurementEdit();
            }
        } else if (ev.key === 'Enter' && this.state.showMeasurementInput) {
            this._saveMeasurementEdit();
        }
    }

    // Wheel event for measurement font size adjustment
    _onWheel(ev) {
        if (this.state.isMeasuring && ev.ctrlKey) {
            ev.preventDefault();
            const delta = Math.sign(ev.deltaY);
            this.state.measurementFontSize = Math.max(8, Math.min(72, this.state.measurementFontSize - delta));
            this._redrawCanvas();
        }
    }

    // Canvas click handler for selecting measurements
    _onCanvasClick(ev) {
        if (!this.state.isMeasuring || this._isMeasuring) return;

        const canvas = this.canvasRef.el;
        if (!canvas) return;

        const rect = canvas.getBoundingClientRect();
        const x = (ev.clientX - rect.left) * (canvas.width / rect.width);
        const y = (ev.clientY - rect.top) * (canvas.height / rect.height);

        // Check if click is on a measurement
        for (const measurement of this.state.measurements) {
            const midX = (measurement.startX + measurement.endX) / 2;
            const midY = (measurement.startY + measurement.endY) / 2;

            // Calculate distance from click to measurement center
            const dx = x - midX;
            const dy = y - midY;
            const distance = Math.sqrt(dx * dx + dy * dy);

            // If click is near measurement text, allow editing
            if (distance < 30) {
                this._startMeasurementEdit(measurement, midX, midY);
                break;
            }
        }
    }

    // Start editing a measurement
    _startMeasurementEdit(measurement, x, y) {
        const canvas = this.canvasRef.el;
        if (!canvas) return;

        // Convert to CSS coordinates
        const rect = canvas.getBoundingClientRect();
        const cssX = (x * rect.width / canvas.width) + rect.left;
        const cssY = (y * rect.height / canvas.height) + rect.top;

        this.state.editingMeasurement = measurement;
        this.state.measurementPosition = { x: cssX, y: cssY };
        this.state.showMeasurementInput = true;

        // Focus input after rendering
        setTimeout(() => {
            const input = this.measurementInputRef && this.measurementInputRef.el;
            if (input) {
                input.value = measurement.value;
                input.focus();
                input.select();
            }
        }, 10);
    }

    // Save measurement edit
    _saveMeasurementEdit() {
        if (!this.state.editingMeasurement) return;

        const input = this.measurementInputRef && this.measurementInputRef.el;
        if (input && input.value.trim()) {
            this.state.editingMeasurement.value = input.value;
            this.state.showMeasurementInput = false;
            this.state.editingMeasurement = null;
            this._redrawCanvas();
            this._saveState().catch(error => {
                console.warn("Failed to save state:", error);
            });
        }
    }

    // Cancel measurement edit
    _cancelMeasurementEdit() {
        this.state.showMeasurementInput = false;
        this.state.editingMeasurement = null;
    }

    // Toggle measurement tool
    _toggleMeasurementTool() {
        const root = this.canvasRef.el?.closest('.o_sketch_widget');
        if (!root) return;

        const measureBtn = root.querySelector('.o_sketch_tool[data-tool="measure"]');
        if (measureBtn) {
            measureBtn.click();
        }
    }

    // Synchronize canvas size with container
    _syncCanvasSize(preserveContent = true) {
        const canvas = this.canvasRef.el;
        const container = this.containerRef.el;

        if (!canvas || !container || !this.ctx) return;

        const dpr = window.devicePixelRatio || 1;
        const rect = container.getBoundingClientRect();
        const cssWidth = Math.max(200, Math.floor(rect.width));
        const cssHeight = Math.max(100, Math.round(cssWidth * 0.66));

        // Check if size actually changed
        if (canvas.width === Math.round(cssWidth * dpr) &&
            canvas.height === Math.round(cssHeight * dpr)) {
            return;
        }

        // Save current content if needed
        let content = null;
        if (preserveContent && canvas.width > 0 && canvas.height > 0) {
            try {
                content = this.ctx.getImageData(0, 0, canvas.width, canvas.height);
            } catch (e) {
                console.warn("Could not get image data:", e);
            }
        }

        // Set new size
        canvas.style.width = `${cssWidth}px`;
        canvas.style.height = `${cssHeight}px`;
        canvas.width = Math.round(cssWidth * dpr);
        canvas.height = Math.round(cssHeight * dpr);

        // Reset transform for high DPI
        this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

        // Restore content if available
        if (content) {
            try {
                // Create temporary canvas to hold old content
                const tempCanvas = document.createElement('canvas');
                tempCanvas.width = content.width;
                tempCanvas.height = content.height;
                const tempCtx = tempCanvas.getContext('2d');
                tempCtx.putImageData(content, 0, 0);

                // Draw scaled content
                this.ctx.drawImage(tempCanvas, 0, 0, cssWidth, cssHeight);
            } catch (e) {
                console.warn("Could not restore content:", e);
                this._fillBackground('#FFFFFF');
            }
        } else {
            // Fill with background
            this._fillBackground('#FFFFFF');
        }

        // Redraw measurements
        this._redrawCanvas();
    }

    // Redraw the entire canvas with measurements
    _redrawCanvas() {
        const canvas = this.canvasRef.el;
        if (!canvas || !this.ctx) return;

        // Restore from history
        this._restoreState();

        // Redraw all measurements
        this.state.measurements.forEach(measurement => {
            this._drawMeasurement(
                measurement.startX, measurement.startY,
                measurement.endX, measurement.endY,
                measurement.value, measurement.unit
            );
        });
    }

    // Pointer event handlers
    _onPointerDown(ev) {
        if (ev.pointerType === "mouse" && ev.button !== 0) return;

        const canvas = this.canvasRef.el;
        if (!canvas) return;

        canvas.setPointerCapture(ev.pointerId);

        const rect = canvas.getBoundingClientRect();
        const x = (ev.clientX - rect.left) * (canvas.width / rect.width);
        const y = (ev.clientY - rect.top) * (canvas.height / rect.height);

        if (this.state.isMeasuring) {
            // Start measurement
            this._isMeasuring = true;
            this._measurementStartX = x;
            this._measurementStartY = y;
            this._measurementEndX = x;
            this._measurementEndY = y;

            // Save state before drawing temporary line
            this._saveTempState();
        } else {
            // Start drawing
            this.isDrawing = true;
            this._lastX = x;
            this._lastY = y;

            // Start drawing immediately
            this.ctx.beginPath();
            this.ctx.moveTo(x, y);
        }
    }

    _onPointerMove(ev) {
        const canvas = this.canvasRef.el;
        if (!canvas) return;

        const rect = canvas.getBoundingClientRect();
        const x = (ev.clientX - rect.left) * (canvas.width / rect.width);
        const y = (ev.clientY - rect.top) * (canvas.height / rect.height);

        if (this._isMeasuring) {
            // Update measurement line
            this._measurementEndX = x;
            this._measurementEndY = y;

            // Draw temporary measurement line
            this._drawTempMeasurementLine();
        } else if (this.isDrawing) {
            // Draw line segment
            this.ctx.lineCap = 'round';
            this.ctx.lineJoin = 'round';
            this.ctx.lineWidth = this.currentWidth;
            this.ctx.strokeStyle = this.currentTool === 'eraser' ? '#FFFFFF' : this.currentColor;

            this.ctx.beginPath();
            this.ctx.moveTo(this._lastX, this._lastY);
            this.ctx.lineTo(x, y);
            this.ctx.stroke();

            // Update last position
            this._lastX = x;
            this._lastY = y;
        }
    }

    _onPointerUp(ev) {
        const canvas = this.canvasRef.el;
        if (canvas) {
            try {
                canvas.releasePointerCapture(ev.pointerId);
            } catch (e) {
                // Ignore errors
            }
        }

        if (this._isMeasuring) {
            // Finish measurement and calculate value
            this._saveMeasurement();
            this._isMeasuring = false;
        } else if (this.isDrawing) {
            this.isDrawing = false;
            this._lastX = null;
            this._lastY = null;
            this._saveState().catch(error => {
                console.warn("Failed to save state:", error);
            });
        }
    }

    // Draw temporary measurement line
    _drawTempMeasurementLine() {
        if (!this._tempMeasurementLine) return;

        // Restore to state before drawing temporary line
        this._restoreTempState();

        // Draw the measurement line
        this.ctx.beginPath();
        this.ctx.moveTo(this._measurementStartX, this._measurementStartY);
        this.ctx.lineTo(this._measurementEndX, this._measurementEndY);
        this.ctx.strokeStyle = this.state.measurementColor;
        this.ctx.lineWidth = 2;
        this.ctx.setLineDash([5, 5]);
        this.ctx.stroke();
        this.ctx.setLineDash([]);

        // Draw endpoints
        this.ctx.beginPath();
        this.ctx.arc(this._measurementStartX, this._measurementStartY, 4, 0, Math.PI * 2);
        this.ctx.arc(this._measurementEndX, this._measurementEndY, 4, 0, Math.PI * 2);
        this.ctx.fillStyle = this.state.measurementColor;
        this.ctx.fill();

        // Draw measurement value
        this._drawMeasurementValue(this._measurementStartX, this._measurementStartY,
                                 this._measurementEndX, this._measurementEndY, true);
    }

    // Draw measurement value
    _drawMeasurementValue(startX, startY, endX, endY, isTemporary = false) {
        // Calculate distance in pixels
        const dx = endX - startX;
        const dy = endY - startY;
        const distance = Math.sqrt(dx * dx + dy * dy);

        // Convert to selected unit (pixels to cm approximation)
        let measurementValue;
        switch(this.state.measurementUnit) {
            case "mm":
                measurementValue = (distance / 3.78).toFixed(1); // Approximation
                break;
            case "cm":
                measurementValue = (distance / 37.8).toFixed(1); // Approximation
                break;
            case "m":
                measurementValue = (distance / 3780).toFixed(2); // Approximation
                break;
            case "in":
                measurementValue = (distance / 96).toFixed(1); // Approximation
                break;
            case "ft":
                measurementValue = (distance / 1152).toFixed(1); // Approximation
                break;
            default:
                measurementValue = distance.toFixed(0);
        }

        // Calculate midpoint for text
        const midX = (startX + endX) / 2;
        const midY = (startY + endY) / 2;

        // Draw measurement text
        this.ctx.font = `${this.state.measurementFontSize}px Arial`;
        this.ctx.fillStyle = isTemporary ? '#888' : this.state.measurementColor;
        this.ctx.textAlign = "center";
        this.ctx.textBaseline = "middle";

        const text = `${measurementValue} ${this.state.measurementUnit}`;
        this.ctx.fillText(text, midX, midY);

        return measurementValue;
    }

    // Draw a complete measurement
    _drawMeasurement(startX, startY, endX, endY, value, unit) {
        // Draw the measurement line
        this.ctx.beginPath();
        this.ctx.moveTo(startX, startY);
        this.ctx.lineTo(endX, endY);
        this.ctx.strokeStyle = this.state.measurementColor;
        this.ctx.lineWidth = 2;
        this.ctx.stroke();

        // Draw endpoints
        this.ctx.beginPath();
        this.ctx.arc(startX, startY, 4, 0, Math.PI * 2);
        this.ctx.arc(endX, endY, 4, 0, Math.PI * 2);
        this.ctx.fillStyle = this.state.measurementColor;
        this.ctx.fill();

        // Calculate midpoint for text
        const midX = (startX + endX) / 2;
        const midY = (startY + endY) / 2;

        // Draw measurement text
        this.ctx.font = `${this.state.measurementFontSize}px Arial`;
        this.ctx.fillStyle = this.state.measurementColor;
        this.ctx.textAlign = "center";
        this.ctx.textBaseline = "middle";

        const text = `${value} ${unit}`;
        this.ctx.fillText(text, midX, midY);
    }

    // Save temporary state for measurement line
    _saveTempState() {
        const canvas = this.canvasRef.el;
        if (!canvas) return;

        try {
            this._tempMeasurementLine = this.ctx.getImageData(0, 0, canvas.width, canvas.height);
        } catch (e) {
            console.warn("Could not save temp state:", e);
        }
    }

    // Restore temporary state
    _restoreTempState() {
        if (!this._tempMeasurementLine) return;

        try {
            this.ctx.putImageData(this._tempMeasurementLine, 0, 0);
        } catch (e) {
            console.warn("Could not restore temp state:", e);
        }
    }

    // Save measurement
    _saveMeasurement() {
        const canvas = this.canvasRef.el;
        if (!canvas) return;

        // Calculate measurement value
        const measurementValue = this._drawMeasurementValue(
            this._measurementStartX, this._measurementStartY,
            this._measurementEndX, this._measurementEndY
        );

        // Store measurement with unique ID
        const measurementId = Date.now() + Math.random().toString(36).substr(2, 9);
        this.state.measurements.push({
            id: measurementId,
            startX: this._measurementStartX,
            startY: this._measurementStartY,
            endX: this._measurementEndX,
            endY: this._measurementEndY,
            value: measurementValue,
            unit: this.state.measurementUnit
        });

        // Draw the final measurement
        this._drawMeasurement(
            this._measurementStartX, this._measurementStartY,
            this._measurementEndX, this._measurementEndY,
            measurementValue, this.state.measurementUnit
        );

        // Reset state
        this._tempMeasurementLine = null;

        // Save to history
        this._saveState().catch(error => {
            console.warn("Failed to save state:", error);
        });
    }

    // Memory-efficient state saving
    async _saveState() {
        const canvas = this.canvasRef.el;
        if (!canvas) return;

        try {
            const dataUrl = canvas.toDataURL("image/png");

            // If we've undone and then drew new content, truncate "future" history
            if (this.historyIndex < this.history.length - 1) {
                this.history = this.history.slice(0, this.historyIndex + 1);
            }

            this.history.push(dataUrl);
            this.historyIndex = this.history.length - 1;

            // Enforce max history length
            while (this.history.length > this.maxHistory) {
                this.history.shift();
                this.historyIndex--;
            }

            this._updateButtonStates();
        } catch (error) {
            console.warn("SketchWidget: _saveState failed", error);
            this._showNotification("Failed to save drawing state", "warning");
        }
    }

    // Update undo/redo button states
    _updateButtonStates() {
        const root = this.canvasRef.el?.closest('.o_sketch_widget');
        if (!root) return;

        const undoBtn = root.querySelector(".o_sketch_undo");
        const redoBtn = root.querySelector(".o_sketch_redo");

        if (undoBtn) {
            undoBtn.disabled = this.historyIndex <= 0;
            undoBtn.setAttribute("aria-disabled", undoBtn.disabled);
        }
        if (redoBtn) {
            redoBtn.disabled = this.historyIndex >= this.history.length - 1;
            redoBtn.setAttribute("aria-disabled", redoBtn.disabled);
        }
    }

    // Restore state from history
    _restoreState() {
        if (this.historyIndex < 0 || this.historyIndex >= this.history.length) return;

        const canvas = this.canvasRef.el;
        if (!canvas || !this.ctx) return;

        const dataUrl = this.history[this.historyIndex];
        if (!dataUrl) return;

        const img = new Image();
        img.onload = () => {
            this.ctx.clearRect(0, 0, canvas.width, canvas.height);
            this.ctx.drawImage(img, 0, 0);
            this._updateButtonStates();
        };
        img.onerror = () => {
            console.warn("Failed to load history state");
            this._fillBackground('#FFFFFF');
        };
        img.src = dataUrl;
    }

    // Fill background
    _fillBackground(color) {
        const canvas = this.canvasRef.el;
        if (!canvas || !this.ctx) return;

        this.ctx.save();
        this.ctx.setTransform(1, 0, 0, 1, 0, 0);
        this.ctx.fillStyle = color;
        this.ctx.fillRect(0, 0, canvas.width, canvas.height);
        this.ctx.restore();

        // Clear measurements
        this.state.measurements = [];
    }

    // Control actions
    _onClear() {
        if (confirm("Are you sure you want to clear the canvas?")) {
            this._fillBackground('#FFFFFF');
            this._saveState().catch(error => {
                console.warn("Failed to save after clear:", error);
            });
        }
    }

    async _onSave() {
        const canvas = this.canvasRef.el;
        if (!canvas) return;

        try {
            canvas.toBlob(async (blob) => {
                try {
                    const reader = new FileReader();
                    reader.onload = async () => {
                        const base64Data = reader.result.split(',')[1];
                        if (this.props.record) {
                            await this.props.record.update({ [this.props.name]: base64Data });
                            this._showNotification("Sketch saved successfully!", "success");
                        }
                    };
                    reader.onerror = () => {
                        throw new Error("Failed to read blob data");
                    };
                    reader.readAsDataURL(blob);
                } catch (error) {
                    console.error("Save process failed:", error);
                    this._showNotification("Failed to save sketch", "danger");
                }
            }, "image/png", this.exportQuality);
        } catch (error) {
            console.error("Save failed:", error);
            this._showNotification("Failed to save sketch", "danger");
        }
    }

    _onUndo() {
        if (this.historyIndex > 0) {
            this.historyIndex--;
            this._restoreState();

            // Also remove the last measurement if it was added
            if (this.state.measurements.length > 0) {
                this.state.measurements.pop();
            }
        }
    }

    _onRedo() {
        if (this.historyIndex < this.history.length - 1) {
            this.historyIndex++;
            this._restoreState();
        }
    }

    // Show notification using Odoo's notification service
    _showNotification(message, type = "info") {
        this.notification.add(message, {
            type: type,
            title: type.charAt(0).toUpperCase() + type.slice(1),
        });
    }

    // Cleanup
    _cleanup() {
        this._isMounted = false;

        // Remove all event listeners
        this._eventListeners.forEach(({ element, event, handler, options }) => {
            if (element) {
                element.removeEventListener(event, handler, options);
            }
        });
        this._eventListeners = [];

        // Cleanup resize observer
        if (this._resizeObserver) {
            this._resizeObserver.disconnect();
            this._resizeObserver = null;
        }

        if (this._resizeDebounce) {
            clearTimeout(this._resizeDebounce);
            this._resizeDebounce = null;
        }

        // Cleanup history
        this.history = [];
        this.historyIndex = -1;
    }
}

CommissionSketchWidget.template = "CommissionSketchWidget";
CommissionSketchWidget.props = {
    record: Object,
    name: String,
};

registry.category("fields").add("commission_sketch", {
    component: CommissionSketchWidget,
});