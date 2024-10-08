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

    function getCollisions(tree, interval) {
        return tree.search(interval);
    }

    function removeMany(tree, values) {
        for(var i = 0; i < values.length; i ++) {
            tree.remove([values[i].low, values[i].high], values[i]);
        }

        return tree;
    }

    function removeCollisions(tree, interval) {
        var others = getCollisions(tree, interval);
        return removeMany(tree, others);
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

            var others = getCollisions(tree, interval)
            tree = removeMany(tree, others);
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
            } else if (annotation.high == i) {
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

    function fromRangeToAnnotation(range) {
        var fragment = range.cloneContents();
        var result = "";
        for(var i = 0; i < fragment.childNodes.length; i ++) {
            var node = fragment.childNodes[i];
            if(node.tagName === 'BR' || node.tagName === 'br') {
                result += '<br>'; // a carriage return might be more formal
            } else if (node.textContent !== '') {
                result += node.textContent;
            } else {
                console.warn("not sure how to annotate:", node.tagName, node);
            }
        }
        
        return result;
    }

    function getSelectedRanges() {
        var selection = window.getSelection();

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

    function removeAnnotations(range) {
        annotations = removeCollisions(annotations, range);
    }

    function updateAnnotations(range) {
        var others = getCollisions(annotations, [range.start, range.end])
        if(others.length == 0) {
            annotations.insert([range.start, range.end], {
                low: range.start,
                high: range.end,
                span: instanceText.substring(range.start, range.end),
                labels: [currentLabel],
                colors: [currentColor]
            });

            return;
        }

        
        annotations = removeMany(annotations, others);
        var group = makeUnique({
            low: range.start,
            high: range.end,
            span: instanceText.substring(range.start, range.end),
            labels: [currentLabel],
            colors: [currentColor]
        }, others);
        annotations = insertMany(annotations, group);
    }

    function collectAndPostRanges(event) {
        var newRanges = getSelectedRanges();
        if(newRanges.length === 0) {
            return;
        }

        console.log("Ranges: ", newRanges)

        for(var i = 0; i < newRanges.length; i ++) {
            if(currentLabel === undefined){
                removeAnnotations(newRanges[i]);
            } else {
                updateAnnotations(newRanges[i]);
            }
        }

        //postJson("/beta-span", toAnnotations(selections)); // ignore promise return
        renderAnnotations();
    }

    function changeSelector(event) {
        var target = event.target;
        if(target.dataset.color === undefined) {
            throw Error("Invalid change event occurred!");
        }

        var setTo = target.checked;

        var inputs = document.querySelectorAll(".new-span-input");
        for(var i = 0; i < inputs.length; i ++) {
            inputs[i].checked = false;
        }

        target.checked = setTo;

        if (setTo) {
            currentColor = target.dataset.color;
            currentLabel = target.dataset.labelContent;
        } else {
            currentColor = undefined;
            currentLabel = undefined;
        }
    }

    var inputs = document.querySelectorAll(".new-span-input");
    for(var i = 0; i < inputs.length; i ++) {
        inputs[i].addEventListener('change', changeSelector);

        if(inputs[i].checked) {
            currentColor = inputs[i].dataset.color;
            currentLabel = inputs[i].dataset.labelContent;
        }
    }

    document.addEventListener('mouseup', collectAndPostRanges);
    document.debug = {};
    document.debug.printAnnotations = function() {
        console.log(annotations.values);
    }
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