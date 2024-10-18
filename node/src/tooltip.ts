// document.addEventListener("ready", () => {

import $ from "jquery";
import "jquery-ui-dist/jquery-ui";

export function jqueryUITooltip() {
    $('[data-toggle="tooltip"]').tooltip();
};