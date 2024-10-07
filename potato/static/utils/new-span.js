/*
 * author: Tristan Hilbert
 * date: 10/4/2024
 * filename: new-span.js
 * desc: Client Side Functionality for new spans. By Grabbing the context for
 *   the problem instance and rendering based on an in-memory model, the span
 *   annotation efficiently collects data.
 */

var instance_text = undefined;
var current_label = undefined;
var current_color = undefined;
var selections = {};

function getInstanceText() {
    try {
        var instanceVarElem = document.getElementById("instance");
        var instanceJson = JSON.parse(instanceVarElem.textContent);
        return instanceJson["text"];
    } catch(e) {
        console.warn("unable to get instance text, was the instance rendered correctly?");
        console.error(e);
    }

    return undefined;
}

function getSpanAnnotations() {
    var selections = {}
    try {
        var spanAnnotationsVarElem = document.getElementById("span-annotations");
        var spanAnnotations = JSON.parse(spanAnnotationsVarElem.textContent);
        var annotation = null;
        var label = "";
        for(var i = 0; i < spanAnnotations.length; i ++) {
            annotation = spanAnnotations[i];
            label = annotation.label;
            selections[label] = [];
            for(j = 0; j < annotation["starts"].length; j ++) {
                selections[label].push({
                    start: annotation["starts"][j],
                    end: annotation["ends"][j]
                });
            }
        }

        return selections;
    } catch(e) {
        console.warn("unable to get span annotations. was the instance rendered correctly?");
        console.log(e);
    }

    return selections;
}

function getSelectedRanges() {
    var selection = window.getSelection();
    var ranges = [];
    var range = null;
    var length = 0;
    var start = 0;
    var offsetCache = 0;
    for(var i = 0; i < selection.rangeCount; i ++) {
        range = selection.getRangeAt(i);
        length = range.toString().length;
        offsetCache = range.startContainer.dataset.offset || 0;
        start = range.startOffset + offsetCache;
        ranges.push({
            start: start, 
            end: start + length,
        });
    }

    return ranges;
}

function collectAndPostRanges(event) {
    var newRanges = getSelectedRanges();
    if(current_label === undefined){
        removeAnnotations(newRanges);
    } else {
        updateAnnotations(newRanges);
    }

    postJson("/beta-span", toAnnotations(selections)); // ignore promise return
    renderAnnotations();
}

function removeAnnotations(newRanges) {
    var keys = Object.keys(selections);
    for(var i = 0; i < keys.length; i ++) { 
        removeAnnotationForLabel(keys[i], newRanges);
    }
}

function removeAnnotationForLabel(label, newRanges) {
    var removal = false;
    var selectionRanges = selection[label];
    for(var i = 0; i < selectionRanges.length; removal ? (removal = false) : i ++) {
        for(var j = 0; j < newRanges.length; j ++) {
            currentSelection.setStart(selectionRange[i].start);
            currentSelection.setEnd(selecitonRange[i].end);
            otherSelection.setStart(newRanges[j].start);
            otherSelection.setEnd(newRanges[j].end);

            
        }
    }
}

function addAnnotations(newRanges) {
    var color = current_color;
    if(color === undefined) {
        throw Error("unable to paint annotations without a color.");
    }

    var start = 0;
    var end = 0;
    var range = null;
    for(var i = 0; i < newRanges.length; i ++) {
        range = newRanges[i];
        start = range.start;
        end = range.start + range.length;
        text = instance_text.substring(start, end);

        annotations.push({
            "displayed_text": text,
            "start": start, 
            "end": end,
            "color": color,
        });
    }
}

function renderAnnotations() {

}

function surroundSelectionNew(selectionLabel, selectionColor)  {
    //var span = document.createElement("span");
    //span.style.fontWeight = "bold";
    //span.style.color = "green";

    if (window.getSelection) {
        // Otherwise, we're going to be adding a new span annotation, if
        // the user has selected some non-empty part of th text
        if (sel.rangeCount && sel.toString().trim().length > 0) {                 

            tsc = selectionColor.replace(")", ", 0.25)")
            
            var span = document.createElement("span");
            span.className = "span_container";
            span.setAttribute("selection_label", selectionLabel);
            span.setAttribute("style", "background-color:rgb" + tsc + ";");
            console.log(selectionColor);
            
            var label = document.createElement("div");
            label.className = "span_label";
            label.textContent = selectionLabel;
            label.setAttribute("style", "background-color:white;"
                            + "border:2px solid rgb" + selectionColor + ";");
            
            var range = sel.getRangeAt(0).cloneRange();
            range.surroundContents(span);
            sel.removeAllRanges();
            sel.addRange(range);
            span.appendChild(label);
        }
    }
}

// main-like function
// (function() {
//     document.addEventListener('mouseup', collectAndPostRanges);
//     instance_text = getInstanceText();
//     selections = getSpanAnnotations();
//     renderAnnotations();  
// })();