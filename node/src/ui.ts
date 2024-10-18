import $ from "jquery";

import VanillaTilt from 'vanilla-tilt';

export function jqueryUITooltip() {
    ($('[data-toggle="tooltip"]') as any).powerTip();
};

export function jqueryTilt() {
    const elements = document.querySelectorAll(".js-tilt");

    VanillaTilt.init(Array.from(elements) as HTMLElement[], {
        scale: 1.1,
    });
}