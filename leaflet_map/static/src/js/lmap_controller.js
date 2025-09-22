/** @odoo-module */
import { Component } from "@odoo/owl";
import { LeafletMapRenderer } from "./lmap_renderer";
import { Layout } from "@web/search/layout";

export class LeafletMapController extends Component {
    static template = "leaflet_map.MapView";
    static components = { LeafletMapRenderer, Layout };
    setup() {
        const arch = this.props.arch;
        const attrs = arch?.attributes;

        this.mapProps = {
            model: attrs?.getNamedItem("model")?.value || "crm.lead",
            fields: attrs?.getNamedItem("fields")?.value?.split(",") || ["id","name","partner_name","latitude","longitude"],
            nameField: attrs?.getNamedItem("name-field")?.value || "partner_name",
            defaultLat: parseFloat(attrs?.getNamedItem("default-lat")?.value) || 8.998093,
            defaultLng: parseFloat(attrs?.getNamedItem("default-lng")?.value) || 38.777651,
            defaultZoom: parseInt(attrs?.getNamedItem("default-zoom")?.value) || 12,
        };

        console.log("Controller mapProps:", this.mapProps);
    }


}
