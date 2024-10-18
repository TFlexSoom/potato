
import $ from "jquery";

function surroundSelection(selectionLabel: string, selectionColor: string)  {
    //var span = document.createElement("span");
    //span.style.fontWeight = "bold";
    //span.style.color = "green";

    if (window.getSelection) {
        var sel = window.getSelection();

        // Check that we're labeling something in the instance text that
        // we want to annotate
        if (! sel?.anchorNode?.parentElement) {
            return
        }

        if (sel.anchorNode.parentElement.getAttribute("name") != "instance_text") {
            // See if this text was already wrapped with the currently
            // selected class label and if so, remove it
            const parentOfSelection = sel.anchorNode.parentElement;
            if(parentOfSelection === null) {
                return;
            }

            if (parentOfSelection.getAttribute("selection_label") == selectionLabel) {
                // Remove the div tag that has the span's annotation label
                $( parentOfSelection ).find("div").remove();
                // Remove the span tag that has the highlight box
                const firstChildElem = parentOfSelection.firstChild;
                if(firstChildElem === null) {
                    return;
                }

                $( firstChildElem ).unwrap();
            }

            return;
        }
        
        // Otherwise, we're going to be adding a new span annotation, if
        // the user has selected some non-empty part of th text
        if (sel.rangeCount && sel.toString().trim().length > 0) {                 

            (window as any).tsc = selectionColor.replace(")", ", 0.25)")
            
            var span = document.createElement("span");
            span.className = "span_container";
            span.setAttribute("selection_label", selectionLabel);
            span.setAttribute("style", "background-color:rgb" + (window as any).tsc + ";");
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

export function changeSpanLabel(checkbox: HTMLInputElement, spanLabel: string, spanColor: string) {
    // Listen for when the user has highlighted some text (only when the label is checked)
    document.addEventListener("mouseup", () => {
        if (checkbox.checked){
            surroundSelection(spanLabel, spanColor);
        }
    });
}