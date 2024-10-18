/*
 * author: Tristan Hilbert
 * date: 10/18/2024
 * filename: view.js
 * desc: In charge of constructing the html to render the proper view tags.
 */

import { AnnotationValue } from "./types";


export function hasSpanAnnotations() {
    try {
        var annotationsHtmlElem = document.getElementById("span-annotations");
        return !!annotationsHtmlElem;
    } catch(e) {
        console.warn("unable to get span annotations. was the instance rendered correctly?");
        console.log(e);
    }

    return false;
}


function renderAnnotationStartTag(annotation: AnnotationValue) {
    var result = "<span class=\"";
    for(var k = 0; k < annotation.colors.length; k ++) {
        result += " new-span-color-" + annotation.colors[k] + " ";
    }

    result += "\" data-labels=\"";

    for(var k = 0; k < annotation.labels.length; k ++) {
        if(k !== 0) {
            result += ",";
        }
        result += annotation.labels[k];
    }

    result += "\">";

    return result;
}

function renderAnnotationEndTag() {
    return "</span>"
}

export function render(annotationBox: HTMLElement, text: string, annotationIter: Iterable<AnnotationValue>) {
    let render = "";
    let annotations = Array.from(annotationIter);
    let i = 0; 
    let j = 0;
    while(i < text.length && j < annotations.length) {
        var annotation = annotations[j];

        if(annotation.start == i) {
            render += renderAnnotationStartTag(annotation);
        } else if (annotation.end == i) {
            render += renderAnnotationEndTag();
            j += 1;
        }

        render += text[i ++];
    }

    while(i < text.length) {
        render += text[i ++];
    }

    console.log(render);

    annotationBox.innerHTML = render;

    console.log(annotationBox.innerHTML);
}