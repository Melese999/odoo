/** @odoo-module */
import { Component, onWillStart, useRef, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { loadJS, loadCSS } from "@web/core/assets";

export class LeafletMapRenderer extends Component {
    static template = "leaflet_map.MapRenderer";

    // Props that can be passed from the controller
    static props = {
        model: String,
        fields: { type: Array },
        nameField: { type: String, optional: true },
        defaultLat: { type: Number, optional: true, default: 8.998093 },
        defaultLng: { type: Number, optional: true, default: 38.777651 },
        defaultZoom: { type: Number, optional: true, default: 12 },
    };

    setup() {
        this.root = useRef("map"); // container ref
        this.orm = useService("orm"); // Odoo ORM service
        this.records = []; // will hold fetched records
        this.map = null;

        // Function to render markers
        const renderMarkers = () => {
            if (!this.map) return;
            this.records.forEach((rec) => {
                if (rec.latitude && rec.longitude) {
                    const marker = L.marker([rec.latitude, rec.longitude]).addTo(this.map);
                    const label = this.props.nameField ? rec[this.props.nameField] : rec.name || "No Name";
                    marker.bindTooltip(`<b>${label}</b>`, { permanent: true, direction: "top", offset: [0, -10] });
                    marker.bindPopup(`<b>${label}</b><br/>Lat: ${rec.latitude}, Lng: ${rec.longitude}`);
                }
            });
        };

        // Load Leaflet CSS and JS before rendering
        onWillStart(async () => {
            await loadCSS("https://unpkg.com/leaflet@1.9.4/dist/leaflet.css");
            await loadJS("https://unpkg.com/leaflet@1.9.4/dist/leaflet.js");

            // Fetch records from Odoo model if props are provided
            if (this.props.model && this.props.fields.length) {
                this.records = await this.orm.searchRead(
                    this.props.model,
                    [],
                    this.props.fields
                );
            }
        });

        // Initialize map and markers after component is mounted
        onMounted(() => {
            let initLat = this.props.defaultLat;
            let initLng = this.props.defaultLng;

            // Center map on first record if available
            const first = this.records.find(r => r.latitude && r.longitude);
            if (first) {
                initLat = first.latitude;
                initLng = first.longitude;
            }

            // Initialize Leaflet map
            this.map = L.map(this.root.el).setView([initLat, initLng], this.props.defaultZoom);

            // Add OpenStreetMap tiles
            L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
                maxZoom: 19,
                attribution: '&copy; OpenStreetMap contributors',
            }).addTo(this.map);

            // Add markers for each record
            renderMarkers();
        });
    }
}
