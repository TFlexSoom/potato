/*
 * author: Tristan Hilbert
 * date: 10/4/2024
 * filename: new-span.js
 * desc: Client Side Functionality for new spans. By Grabbing the context for
 *   the problem instance and rendering based on an in-memory model, the span
 *   annotation efficiently collects data.
 */

import { getElementById, getJsonElement } from "../document";
import { render } from "./view";

interface ColorLabel {
    color: number
    label: string
}

let instanceText = "";
let annotationBox: HTMLElement | undefined = undefined;
let current: ColorLabel | undefined = undefined;

function fromRangeToAnnotation(range: Range) {
    var fragment = range.cloneContents();
    var result = "";
    for(var i = 0; i < fragment.childNodes.length; i ++) {
        var elem = fragment.children[i];
        if(elem.tagName === 'BR' || elem.tagName === 'br') {
            result += '<br>'; // a carriage return might be more formal
        } else if (elem.textContent !== '') {
            result += elem.textContent;
        } else {
            console.warn("not sure how to annotate:", elem.tagName, elem);
        }
    }
    
    return result;
}


function getSelectedRanges() {
    var selection = window.getSelection();
    if(annotationBox === undefined || selection === null) {
        return [];
    }

    if(!annotationBox.contains(selection.anchorNode)) {
        return [];
    }

    var ranges = [];
    for(var i = 0; i < selection.rangeCount; i ++) {
        var range = selection.getRangeAt(i);
        
        // create second highlight to get char length
        var startOffsetRange = range.cloneRange();
        startOffsetRange.selectNodeContents(annotationBox);
        startOffsetRange.setEnd(range.endContainer, range.endOffset);
        
        var rangeLength = fromRangeToAnnotation(range).length;
        var start = fromRangeToAnnotation(startOffsetRange).length - rangeLength;
        var length = Math.min(rangeLength, instanceText.length - start);

        if(length === 0) {
            continue;
        }

        ranges.push({
            start: start, 
            end: start + length,
        });
    }

    return ranges;
}

function addClickupEventToText(annotationBoxLocal: HTMLElement) {
    if(annotationBox === undefined) {
        return;
    }

    annotationBoxLocal.addEventListener("click", () => {
        var selections = getSelectedRanges();
        if(selections.length === 0) {
            return;
        }

        for(const selection of selections) {
            appendSelection(selection, current);
        }

        consolidateAndRender();
    });
}

function addChangeEventToInputs(document: Document) {
    var inputs = document.querySelectorAll("input.new-span-input") as NodeListOf<HTMLInputElement>;
    for(const input of inputs) {
        input.addEventListener('change', (event) => {
            var target = event.target as HTMLInputElement;
            if(target === null || target.dataset.color === undefined) {
                console.warn("Bad Input Change for new-span controller")
                return;
            }

            var setTo = target.checked;
            uncheckOtherSpansInputs();
            target.checked = setTo;
            current = getCurrentLabelAndColor();
        });
    }
}

function consolidateAndRender() {
    const consolidatedRanges = getRanges();
    sendRangesToNetwork(consolidatedRanges);
    render(consolidatedRanges);
}

function uncheckOtherSpansInputs() {
    let inputElems = document.querySelectorAll("input.new-span-input:checked") as NodeListOf<HTMLInputElement>;
    for(const inputElem of inputElems) {
        inputElem.checked = false;
    }
}

function getCurrentLabelAndColor(): ColorLabel | undefined {
    let inputElems = document.querySelectorAll("input.new-span-input:checked");
    if(inputElems.length === 0) {
        return undefined;
    }

    const input = inputElems[0] as HTMLInputElement;

    return {
        color: Number.parseInt(input.dataset.color || "0"),
        label: input.dataset.labelContent || "",
    }
}

export function onReady(document: Document) {
    instanceText = getJsonElement("instance") || "";
    annotationBox = getElementById("instance-text") || undefined;
    let serverAnnotations = getJsonElement("span-annotations") || undefined;
    if(instanceText === "" || annotationBox === undefined || serverAnnotations === undefined) {
        throw Error(`Controller could not initialize ${instanceText} ${annotationBox} ${serverAnnotations}`);
    }

    addChangeEventToInputs(document);
    addClickupEventToText(annotationBox);
    
    current = getCurrentLabelAndColor();

    appendServerAnnotations(serverAnnotations);
    consolidateAndRender();
}