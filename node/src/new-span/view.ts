


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

export function render(ranges: any) {

}