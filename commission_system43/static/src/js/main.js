console.log("✅ Commission System: Main module loaded");

// Global commission system object
window.CommissionSystem = {
    version: '0.1.1',
    initialized: false,
    config: {
        debug: true,
        features: {
            kanban: true,
            sketching: true,
            reporting: true
        }
    }
};

function safeInitialize() {
    console.log("💰 Commission System initializing safely...");

    if (typeof odoo !== 'undefined' && window.CommissionSystem) {
        console.log("✅ Odoo environment detected");

        // Initialize commission system
        initializeCommissionFeatures();

        // Add global event listeners
        setupGlobalListeners();

        // Mark as initialized
        window.CommissionSystem.initialized = true;
        console.log("🚀 Commission System fully initialized!");

    } else {
        console.log("⚠️ Odoo environment not detected yet, retrying...");
        setTimeout(safeInitialize, 1000);
    }
}

function initializeCommissionFeatures() {
    console.log("🛠️ Initializing commission features...");

    // Add commission menu item if doesn't exist
    addCommissionMenu();

    // Initialize any other features here
    initializeCommissionShortcuts();
}

function addCommissionMenu() {
    try {
        // Wait for the main menu to load
        setTimeout(() => {
            const $menu = $('.o_menu_sections');
            if ($menu.length && !$menu.find('.o_commission_menu').length) {
                const menuItem = `
                    <li class="o_menu_item o_commission_menu">
                        <a href="#" class="o_menu_item">
                            <i class="fa fa-money me-2"></i>
                            <span>Commissions</span>
                        </a>
                    </li>
                `;
                $menu.append(menuItem);
                console.log("✅ Commission menu item added");
            }
        }, 3000);
    } catch (error) {
        console.error("❌ Error adding commission menu:", error);
    }
}

function initializeCommissionShortcuts() {
    // Add keyboard shortcuts for commission system
    $(document).on('keydown', function(e) {
        // Ctrl+Shift+C for commission quick access
        if (e.ctrlKey && e.shiftKey && e.key === 'C') {
            e.preventDefault();
            console.log("🎯 Commission quick access activated");
            showQuickCommissionPanel();
        }
    });
}

function showQuickCommissionPanel() {
    const panel = document.createElement('div');
    panel.innerHTML = `
        <div style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); 
                   background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.2);
                   z-index: 10000; min-width: 300px;">
            <h5>💰 Commission Quick Access</h5>
            <p>Commission system is active and working!</p>
            <button onclick="this.parentElement.remove()" class="btn btn-sm btn-primary">
                Close
            </button>
        </div>
    `;
    document.body.appendChild(panel);
}

function setupGlobalListeners() {
    console.log("📡 Setting up global commission listeners");

    // Listen for Odoo events
    $(document).on('commission:update', function(e, data) {
        console.log("📊 Commission update received:", data);
    });

    // Example: Listen for sales order changes
    setInterval(() => {
        // Check for new commission data periodically
        checkForCommissionUpdates();
    }, 30000);
}

function checkForCommissionUpdates() {
    if (window.CommissionSystem.debug) {
        console.log("🔍 Checking for commission updates...");
    }
}

// Start safe initialization
setTimeout(safeInitialize, 2000);

// Export for global access
window.CommissionSystem.initialize = safeInitialize;


// Add to your main.js file
function initializeSketchShortcuts() {
    // Global keyboard shortcuts for sketch widget
    $(document).on('keydown', function(e) {
        // Ctrl+Z for undo
        if (e.ctrlKey && e.key === 'z') {
            e.preventDefault();
            $('.o_sketch_undo').click();
        }

        // Ctrl+Y for redo
        if (e.ctrlKey && e.key === 'y') {
            e.preventDefault();
            $('.o_sketch_redo').click();
        }

        // Ctrl+S for save
        if (e.ctrlKey && e.key === 's') {
            e.preventDefault();
            $('.o_sketch_save').click();
        }

        // E for eraser
        if (e.key === 'e' || e.key === 'E') {
            e.preventDefault();
            $('.o_sketch_tool[data-tool="eraser"]').click();
        }

        // P for pen
        if (e.key === 'p' || e.key === 'P') {
            e.preventDefault();
            $('.o_sketch_tool[data-tool="pen"]').click();
        }
    });

    console.log("⌨️ Sketch keyboard shortcuts initialized");
}

// Call this in your safeInitialize function
function initializeCommissionFeatures() {
    console.log("🛠️ Initializing commission features...");

    addCommissionMenu();
    initializeCommissionShortcuts();
    initializeSketchShortcuts(); // Add this line
}