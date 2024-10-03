function getSelectedText() {
    var text = "";
    if (typeof window.getSelection != "undefined") {
        text = window.getSelection().toString();
    } else if (typeof document.selection != "undefined" && document.selection.type == "Text") {
        text = document.selection.createRange().text;
    }
    return text;
}

function surroundSelection(selectionLabel, selectionColor)  {
    //var span = document.createElement("span");
    //span.style.fontWeight = "bold";
    //span.style.color = "green";

    if (window.getSelection) {
        var sel = window.getSelection();

        // Check that we're labeling something in the instance text that
        // we want to annotate
        if (sel.anchorNode.parentElement) {

            if (sel.anchorNode.parentElement.getAttribute("name") != "instance_text") {
                
                // See if this text was already wrapped with the currently
                // selected class label and if so, remove it
                var parentOfSelection = sel.anchorNode.parentElement

                if (parentOfSelection.getAttribute("selection_label") == selectionLabel) {
                    // Remove the div tag that has the span's annotation label
                    $( parentOfSelection ).find("div").remove();
                    // Remove the span tag that has the highlight box
                    $( parentOfSelection.firstChild ).unwrap();
                }

                return;
            }
        }
        else {
            // alert("no parent element");
            return;
        }
        
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

function changeSpanLabel(checkbox, spanLabel, spanColor) {
    // Listen for when the user has highlighted some text (only when the label is checked)
    document.onmouseup = function() {
        if (checkbox.checked){
            surroundSelection(spanLabel, spanColor);
        }
    }
}

// Listen for when the user has highlighted some text
// document.onmouseup = function() { surroundSelection("Undefined"); } 
