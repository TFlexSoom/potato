/*
 * author: Tristan Hilbert
 * date: 10/4/2024
 * filename: controller.js
 * desc: Client Side Controller Functionality for new spans. By Grabbing the context for
 *   the problem instance and rendering based on an in-memory model, the span
 *   annotation efficiently collects data.
 */

import { Interval } from "@flatten-js/interval-tree";
import { getElementById, getJsonElement } from "../document";
import { AnnotationValue, appendSelections, appendServerAnnotations, ColorLabel, getInstanceTextLength, getRanges, setCurrent, setInstanceText } from "./model";
import { sendRangesToNetwork } from "./network";
import { render } from "./view";

let annotationBox: HTMLElement | undefined = undefined;

export function onReady(document: Document) {
    let instanceText = (getJsonElement("instance") as {text:string})?.text || "";
    annotationBox = getElementById("instance-text") || undefined;
    let serverAnnotations = getJsonElement("span-annotations") || undefined;
    if(instanceText === "" || annotationBox === undefined || serverAnnotations === undefined) {
        throw Error(`Controller could not initialize ${instanceText} ${annotationBox} ${serverAnnotations}`);
    }

    setInstanceText(instanceText);
    setCurrent(getCurrentLabelAndColor());

    addChangeEventToInputs(document);
    addClickupEventToText(annotationBox);

    appendServerAnnotations(serverAnnotations as AnnotationValue[]);
    consolidateAndRender();
}

function textContentWithLinebreaks(range: Range) {
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


function getSelections() {
    var selection = window.getSelection();
    if(annotationBox === undefined || selection === null) {
        return [];
    }

    if(!annotationBox.contains(selection.anchorNode)) {
        return [];
    }

    var intervals = [];
    for(var i = 0; i < selection.rangeCount; i ++) {
        var range = selection.getRangeAt(i);
        
        // create second highlight to get char length
        var startOffsetRange = range.cloneRange();
        startOffsetRange.selectNodeContents(annotationBox);
        startOffsetRange.setEnd(range.endContainer, range.endOffset);
        
        var rangeLength = textContentWithLinebreaks(range).length;
        var start = textContentWithLinebreaks(startOffsetRange).length - rangeLength;
        var length = Math.min(rangeLength, getInstanceTextLength() - start);

        if(length === 0) {
            continue;
        }

        intervals.push(new Interval(start, start + length));
    }

    return intervals;
}

function addClickupEventToText(annotationBoxLocal: HTMLElement) {
    if(annotationBox === undefined) {
        return;
    }

    annotationBoxLocal.addEventListener("click", () => {
        var selections = getSelections();
        if(selections.length === 0) {
            return;
        }

        appendSelections(selections);
        consolidateAndRender();
    });
}

function addChangeEventToInputs(document: Document) {
    var inputs = document.querySelectorAll("input.new-span-input") as NodeListOf<HTMLInputElement>;
    for(const input of inputs) {
        input.addEventListener('change', (event) => {
            var target = event.target as HTMLInputElement;
            if(target === null || target.dataset.color === undefined) {
                console.error("Bad Input Change for new-span controller")
                return;
            }

            let checkedInputs = document.querySelectorAll("input.new-span-input:checked") as NodeListOf<HTMLInputElement>;
            for(const checked of checkedInputs) {
                if(checked === target) {
                    continue;
                }

                checked.checked = false;
            }

            setCurrent(deriveCurrentLabelAndColor(target));
        });
    }
}

function consolidateAndRender() {
    const consolidatedRanges = getRanges();
    sendRangesToNetwork(consolidatedRanges);
    render(consolidatedRanges);
}

function getCurrentLabelAndColor(): ColorLabel | undefined {
    let inputElems = document.querySelectorAll("input.new-span-input:checked") as NodeListOf<HTMLInputElement>;
    if(inputElems.length === 0) {
        return undefined;
    }

    return deriveCurrentLabelAndColor(inputElems[0]);
}

function deriveCurrentLabelAndColor(input: HTMLInputElement): ColorLabel | undefined {
    if(!input.checked) {
        return undefined;
    }

    return {
        color: Number.parseInt(input.dataset.color || "0"),
        label: input.dataset.labelContent || "",
    }
}