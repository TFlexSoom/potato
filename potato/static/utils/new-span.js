/*
 * author: Tristan Hilbert
 * date: 10/4/2024
 * filename: new-span.js
 * desc: Client Side Functionality for new spans. By Grabbing the context for
 *   the problem instance and rendering based on an in-memory model, the span
 *   annotation efficiently collects data.
 */

(function() {
    var instanceText = undefined;
    var annotationBox = undefined;
    var currentLabel = undefined;
    var currentColor = undefined;
    var annotations = null;

    function getInstanceText() {
        try {
            var instanceVarElem = document.getElementById("instance");
            var instanceJson = JSON.parse(instanceVarElem.innerHTML);
            return instanceJson["text"];
        } catch(e) {
            console.warn("unable to get instance text, was the instance rendered correctly?");
            console.error(e);
        }

        return undefined;
    }

    function getAnnotationBox() {
        try {
            return document.getElementById("instance-text");
        } catch(e) {
            console.warn("unable to get annotation box. Was the layout changed?");
            console.error(e);
        }

        return undefined;
    }

    function insertOne(tree, interval, value) {
        tree.insert(interval, {
            low: value.start,
            high: value.end,
            span: value.span,
            labels: [value.label],
            colors: [value.color]
        });

        return tree;
    }

    function insertMany(tree, values) {
        for(var i = 0; i < values.length; i ++) {
            var value = values[i];
            var interval = [value.low, value.high]
            if(tree.intersect_any(interval)) {
                throw Error("Collision Detection in Spans!");
            }

            tree.insert(interval, value);
        }

        return tree;
    }

    function removeCollisions(tree, interval) {
        return tree.search(interval);
    }

    function makeUnique(perpetrator, victims) {
        // The Perpetrator collides with all victims
        // none of the victims collide with eachother
        // create a unique set of inserts where no one collides

        var unmet = new document.potato.IntervalTree();
        var perpLow = perpetrator["start"];
        var perpHigh = perpetrator["end"];
        unmet.insert([perpLow, perpHigh], [perpLow, perpHigh]);
        var result = [];
        for(var i = 0; i < victims.length; i ++) {
            var victim = victims[i];
            var hits = unmet.search([victim.low, victim.high]) // there will only ever be 1 hit
            if (hits.length > 1) {
                throw Error("Tristan's Algorithm is wrong");
            }

            var hitLow = hits[0][0];
            var hitHigh = hits[0][1];
            unmet.remove([hitLow, hitHigh]);

            if(victim.low < hitLow) {
                result.push({
                    low: victim.low,
                    high: hitLow,
                    span: victim.span.substring(0, hitLow - victim.low),
                    labels: victim.labels,
                    colors: victim.colors,
                });

                result.push({
                    low: hitLow,
                    high: victim.high,
                    span: victim.span.substring(hitLow - victim.low),
                    labels: victim.labels + perpetrator.labels
                });

                unmet.insert([victim.high, hitHigh], [victim.high, hitHigh]);
            } else if (victim.high > hitHigh) {
                result.push({
                    low: hitHigh,
                    high: victim.high,
                    span: victim.span.substring(hitHigh - victim.low),
                    labels: victim.labels,
                    colors: victim.colors,
                });

                result.push({
                    low: victim.low,
                    high: hitHigh,
                    span: victim.span.substring(0,  hitHigh - victim.low),
                    labels: victim.labels + perpetrator.labels
                });

                unmet.insert([hitLow, victim.low], [hitLow, victim.low]);
            } else if (victim.low === hitLow && victim.high === hitHigh){
                result.push({
                    low: hitLow,
                    high: hitHigh,
                    span: victim.span,
                    labels: victim.labels + perpetrator.labels,
                    colors: victim.colors + perpetrator.colors,
                });
            } else {
                result.push({
                    low: victim.low,
                    high: victim.high,
                    span: victim.span,
                    labels: victim.labels + perpetrator.labels,
                    colors: victim.colors + perpetrator.colors,
                });

                if(hitLow !== victim.low) {
                    unmet.insert([hitLow, victim.low], [hitLow, victim.low]);
                }

                if(hitHigh !== victim.high) {
                    unmet.insert([victim.high, hitHigh], [victim.high, hitHigh]);
                }
            }
        }

        for(var i = 0; i < unmet.keys.length; i ++) {
            var hit = unmet.keys[i];

            result.push({
                low: hit[0],
                high: hit[1],
                span: perpetrator.span.substring(hit[0] - perpLow, hit[1] - perpLow),
                labels: perpetrator.labels,
                colors: perpetrator.colors
            });
        }

        return result;
    }

    function fromJson(json) {
        // See https://www.npmjs.com/package/@flatten-js/interval-tree
        var tree = new document.potato.IntervalTree();

        for(var i = 0; i < json.length; i ++) {
            var value = json[i];
            var interval = [item["start"], item["end"]];
            if(!tree.intersect_any(interval)) {
                tree = insertOne(tree, interval, value);
                continue;
            }

            var others = removeCollisions(tree, interval)
            group = makeUnique(value, others);
            tree = insertMany(tree, group);
        }

        return tree;
    }

    function hasSpanAnnotations() {
        try {
            var annotationsHtmlElem = document.getElementById("span-annotations");
            return !!annotationsHtmlElem;
        } catch(e) {
            console.warn("unable to get span annotations. was the instance rendered correctly?");
            console.log(e);
        }

        return false;
    }

    function getSpanAnnotations() {
        try {
            var annotationsHtmlElem = document.getElementById("span-annotations");
            var annotationsJson = JSON.parse(annotationsHtmlElem.textContent);
            return fromJson(annotationsJson);
        } catch(e) {
            console.warn("unable to get span annotations. was the instance rendered correctly?");
            console.log(e);
        }

        return null;
    }

    function renderAnnotationStartTag(annotation) {
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

    function renderAnnotations() {
        var render = "";
        var text = instanceText;
        var i = 0; 
        var j = 0;
        while(i < text.length && j < annotations.values.length) {
            var annotation = annotations.values[j];
            if(annotation.low == i) {
                render += renderAnnotationStartTag(annotation);
            } else if (annotation.high == j) {
                render += renderAnnotationEndTag();
                j += 1;
            }

            render += text[i ++];
        }

        while(i < text.length) {
            render += text[i ++];
        }

        annotationBox.innerHTML = render;
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
        if(currentLabel === undefined){
            removeAnnotations(newRanges);
        } else {
            updateAnnotations(newRanges);
        }

        //postJson("/beta-span", toAnnotations(selections)); // ignore promise return
        renderAnnotations();
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

    function changeSelector(event) {
        var target = event.target;
        if(target.dataset.color === undefined) {
            throw Error("Invalid change event occurred!");
        }

        var inputs = document.querySelectorAll(".new-span-input");
        for(var i = 0; i < inputs.length; i ++) {
            inputs[i].checked = false;
        }

        target.checked = true;
        currentColor = target.dataset.color;
        currentLabel = target.dataset.labelContent;
        console.log(currentColor, currentLabel)
    }

    var inputs = document.querySelectorAll(".new-span-input");
    for(var i = 0; i < inputs.length; i ++) {
        inputs[i].addEventListener('change', changeSelector);
    }

    //document.addEventListener('mouseup', collectAndPostRanges);
    instanceText = getInstanceText();
    annotationBox = getAnnotationBox();
    annotations = getSpanAnnotations();

    // Because the original span changes the actual html document, 
    // we need to overwrite the html to allow for our changes to take
    // hold for the new beta highlighting
    if(instanceText !== undefined && annotationBox !== undefined && hasSpanAnnotations()) {
        annotationBox.innerHTML = instanceText;
        renderAnnotations();
    }
})();