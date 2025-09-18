/** @odoo-module */

import { Component, onWillStart, useRef, onMounted } from "@odoo/owl";
import { loadJS, loadCSS } from "@web/core/assets";
import { useService } from "@web/core/utils/hooks";

export class LeafletMapRenderer extends Component {
    static template = "leaflet_map.MapRenderer";
    static props = {};

    setup() {
        this.root = useRef("map");
        this.orm = useService("orm");
        this.records = [];

        // Load leaflet + fetch records
        onWillStart(async () => {
            await loadCSS("https://unpkg.com/leaflet@1.9.4/dist/leaflet.css");
            await loadJS("https://unpkg.com/leaflet@1.9.4/dist/leaflet.js");
            // Fetch crm.lead data (adapt fields if needed)
            this.records = await this.orm.searchRead("crm.lead", [], [
                "id",
                "name",
                "partner_name",
                "latitude",
                "longitude",
            ]);
        });

        // Render map once DOM is ready
        onMounted(() => {
            this.map = L.map(this.root.el).setView([8.998093, 38.777651], 12);

            L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
                maxZoom: 19,
                attribution:
                    '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
            }).addTo(this.map);

            // Add  markers
            this.records.forEach((rec) => {
                if (rec.latitude && rec.longitude) {
                    const marker = L.marker([
                        rec.latitude,
                        rec.longitude,
                    ]).addTo(this.map);

               marker.bindTooltip(
            `<b>${rec.name || "No Name"}</b>`,
            { permanent: true, direction: "top", offset: [0, -10] }
        );

                    marker.bindPopup(`
                        <b>${rec.name || "No Name"}</b><br/>
                        Customer: ${rec.partner_name || "Unknown"}<br/>
                        Lat: ${rec.latitude}, Lng: ${rec.longitude}<br/><br/>
                        <a href="/web#id=${rec.id}&model=crm.lead&view_type=form" 
                           class="btn btn-primary btn-sm text-white">Open</a>
                    `);
                }
            });
        });
    }
}
