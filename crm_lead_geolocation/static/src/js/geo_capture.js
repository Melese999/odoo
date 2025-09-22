/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { onMounted } from "@odoo/owl";

patch(FormController.prototype, {
    setup() {
        super.setup(...arguments)
        onMounted(() => {
            if (this.model.root.resModel === "crm.lead") {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        if (
                            this.model.root.fields.latitude &&
                            this.model.root.fields.longitude
                        ) {
                            this.model.root.update({
                                latitude: +position.coords.latitude.toFixed(6),
                                longitude: +position.coords.longitude.toFixed(6),
                            });
                        }
                    },
                    (err) => {
                        console.warn("Geolocation error:", err);
                    }
                );
            }
        }
        });
    },
});
