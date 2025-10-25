// commission_system/static/src/js/commission_line_kanban.js
console.log("✅ Commission Line Kanban: Module loaded");

// Safe wrapper to prevent errors
function safelyLoadKanban() {
    try {
        // Check if required modules are available
        if (typeof odoo === 'undefined' || !odoo.require) {
            console.log("⚠️ Odoo not ready, retrying...");
            setTimeout(safelyLoadKanban, 1000);
            return;
        }

        // Load dependencies safely
        odoo.require(['web.core', 'web.AbstractField', 'web.field_registry'],
            function(core, AbstractField, fieldRegistry) {
                try {
                    console.log("✅ Dependencies loaded for Commission Line Kanban");

                    const CommissionLineKanban = AbstractField.extend({
                        template: 'CommissionLineKanban',

                        init: function (parent, name, record, options) {
                            this._super.apply(this, arguments);
                            console.log("💰 Commission Line Kanban initialized:", name);
                        },

                        _render: function () {
                            try {
                                this._super.apply(this, arguments);
                                console.log("🎨 Commission Line Kanban rendered");
                            } catch (error) {
                                console.error("❌ Error rendering kanban:", error);
                            }
                        }
                    });

                    // Register the field
                    fieldRegistry.add('commission_line_kanban', CommissionLineKanban);
                    console.log("✅ Commission Line Kanban registered successfully");

                } catch (error) {
                    console.error("❌ Error creating CommissionLineKanban:", error);
                }
            },
            function(error) {
                console.error("❌ Failed to load dependencies:", error);
            }
        );

    } catch (error) {
        console.error("❌ Error in safelyLoadKanban:", error);
    }
}

// Start loading after delay
setTimeout(safelyLoadKanban, 2000);