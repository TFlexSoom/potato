
import $ from "jquery";

/**
 * Sends the current state of the instance's annotation to the server,
 * along with any relevant key presses to request a new instance to
 * annotate.
 */
function get_new_instance(event: KeyboardEvent) {
    var x = event.key;
    var action = ""
    var ism = ""

    //console.log(x)
    //console.log(firstname)
    //console.log(lastname)
    if (x == "ArrowLeft") { // Spacebar
        action = "prev_instance";
    }
    else if (x == "ArrowRight") {
        if (validateForm() == true && validate_answers() == true) {
            action = "next_instance";
        }
        else {
            return;
        }
    }
    else {
        // console.log("Unknown key press", event)
        return;
    }

    const instanceIdElement = document.getElementById('instance_id') as HTMLInputElement;
    if (instanceIdElement === null) {
        return;
    }

    const timeCounterElement = document.getElementById("timecounter");
    if (timeCounterElement === null) {
        return;
    }

    var instance_id = instanceIdElement.value
    var time_string = timeCounterElement.innerHTML //get time spent on this instance
    //time_string = '-1'
    var post_req = {
        label: ism,
        src: action,
        instance_id: instance_id,
        behavior_time_string: time_string
    }

    // Sends the post message to the server which will let us update the
    // currently displayed content
    post(post_req)
}

// document.addEventListener('keyup', 
export function keyupListener(event: KeyboardEvent) {
    const active_id = document.activeElement?.id || "";
    const active_type = document.activeElement?.getAttribute('type') || "";
    if (active_id === 'go_to' || active_type == 'text') return;

    //first check whether this keyboard input is a shortcut for checkboxes
    const checkboxes = document.querySelectorAll('input[type=checkbox]') as NodeListOf<HTMLInputElement>;
    const radios = document.querySelectorAll('input[type=radio]') as NodeListOf<HTMLInputElement>;
    const x = event.key.toLowerCase();

    for (var i = 0; i < checkboxes.length; i++) {
        //alert(checkboxes[i].value)
        if (x === checkboxes[i].value) {
            checkboxes[i].checked = !checkboxes[i].checked;
            if (checkboxes[i].onclick !== null) {
                (checkboxes[i].onclick as any).apply(checkboxes[i]);
            }
            return;
        };
    }
    for (var i = 0; i < radios.length; i++) {
        //alert(checkboxes[i].value)
        if (x === radios[i].value) {
            radios[i].checked = !radios[i].checked;
            if (radios[i].onclick != null) {
                (radios[i].onclick as any).apply(radios[i]);
            }
            return;
        };
    }

    // Each time we process a user's key presses, track who is doing
    // it by grabbing the hidden firstname and lastname fields
    get_new_instance(event);
}

export function click_to_next() {
    // Gacky code to simulate the submit button as a keyboard event
    // and not have two separate paths to handle keyboard and mouse
    // events
    var e = new KeyboardEvent("keyup", {
        key: "ArrowRight",
    });

    get_new_instance(e);
}

export function click_to_prev() {
    // Gacky code to simulate the submit button as a keyboard event
    // and not have two separate paths to handle keyboard and mouse
    // events
    var e = new KeyboardEvent("keyup", {
        key: "ArrowLeft",
    });

    get_new_instance(e);
}

// window.onunload = check_close;

export function check_close() {
    // console.error("session closed");
    var post_req = {
        is_close: "closed"
    }
    post(post_req);
}

// We submit a new post to the same (user/annotate) endpoint
function post(params: Record<string, string>) {

    // The rest of this code assumes you are not using a library.
    // It can be made less wordy if you use one.
    var form = document.createElement("form");
    form.setAttribute("method", "post");
    form.setAttribute("action", "annotate");

    var usernameField = document.getElementById('username') as HTMLInputElement;
    if (usernameField === null) {
        return;
    }

    var hiddenField = document.createElement("input");
    hiddenField.setAttribute("type", "hidden");
    hiddenField.setAttribute("name", "email");
    hiddenField.setAttribute("value", usernameField.value);
    form.appendChild(hiddenField);

    for (var key in params) {
        if (params.hasOwnProperty(key)) {
            var hiddenField = document.createElement("input");
            hiddenField.setAttribute("type", "hidden");
            hiddenField.setAttribute("name", key);
            hiddenField.setAttribute("value", params[key]);

            form.appendChild(hiddenField);
        }
    }

    // Stuff all the current annotations into attributes for processing on the server side
    document.querySelectorAll('form input, form select, form textarea').forEach((inputElem) => {
        let input = inputElem as HTMLInputElement;

        if (input.getAttribute('type') === 'checkbox' || input.getAttribute('type') === 'radio') {
            if (input.checked) {
                // Stuff all the input fields into something for the post
                var hiddenField = document.createElement("input");
                hiddenField.setAttribute("type", "hidden");
                hiddenField.setAttribute("name", input.getAttribute('name') || "");
                hiddenField.setAttribute("value", input.getAttribute('value') || "");
                form.appendChild(hiddenField);
            }
        }
        else if (input.getAttribute('type') == 'text' || input.getAttribute('type') == 'number') {
            var hiddenField = document.createElement("input");
            hiddenField.setAttribute("type", "hidden");
            hiddenField.setAttribute("name", input.getAttribute('name') || "");
            hiddenField.setAttribute("value", input.value);
            form.appendChild(hiddenField);
        }
        else if (input.getAttribute('type') == 'range') {
            var hiddenField = document.createElement("input");
            hiddenField.setAttribute("type", "hidden");
            hiddenField.setAttribute("name", input.getAttribute('name') || "");
            hiddenField.setAttribute("value", input.value);
            form.appendChild(hiddenField);
        }
        else if (input.getAttribute('type') == 'select-one') {
            //alert(input[0].value)
            var hiddenField = document.createElement("input");
            hiddenField.setAttribute("type", "hidden");
            hiddenField.setAttribute("name", input.getAttribute('name') || "");
            hiddenField.setAttribute("value", input.value);
            form.appendChild(hiddenField);
        }
        else {
            console.log("unknown form type: \"" + input.getAttribute('type') + "\"")
        }
    });

    // Get all the highlighted text for this instance and marshall that
    // into some kind of representation for the server side
    const spanContainerElements = document.querySelectorAll(".span_container");
    if (spanContainerElements.length === 0) {
        return;
    }

    // we save the outerHTML to accomadate user-defined HTML inputs,
    // otherwise we just save the plain text
    const span = spanContainerElements[0];
    const spanAttribute = (
        span.parentElement?.parentElement?.getAttribute("name")
    );

    if (spanAttribute === "instance_text") {
        var annotated_spans = span.parentElement?.outerHTML;
    } else {
        var annotated_spans = span.parentElement?.innerHTML;
    }

    var hiddenField = document.createElement("input");
    hiddenField.setAttribute("type", "hidden");
    hiddenField.setAttribute("name", "span-annotation");
    hiddenField.setAttribute("value", annotated_spans || "");
    form.appendChild(hiddenField);

    document.body.appendChild(form);
    form.submit();
}

/**
 * Validate if the user has completed each row for multi-rate schema
 */
function validateForm() {
    var rows = document.querySelectorAll("tr[schema='multirate']");
    for (var i = 0; i < rows.length; i++) {
        var inputs = rows[i].querySelectorAll("input[type='radio'][validation='required']") as NodeListOf<HTMLInputElement>;
        if (inputs.length > 0) {
            var checked = Array.from(inputs).some(input => input.checked);
        } else {
            var checked = true;
        }

        if (!checked) {
            alert("Please complete all the require fields");
            return false;
        }
    }
    return true;
}


/**
* Validate if the input answers meet certain rules
* along with any relevant key presses to request a new instance to
* annotate.
*/
function validate_answers() {

    // check if all the right labels are checked
    //alert({{instance_obj|tojson}}['id'])
    var inputs = document.querySelectorAll('input[validation=right_label]') as NodeListOf<HTMLInputElement>;
    for (var i = 0; i < inputs.length; ++i) {
        if (inputs[i].getAttribute('validation') == 'right_label' && inputs[i].checked == false) {
            alert(inputs[i].name + " must be selected to proceed");
            //alert(instance_obj.id)
            return false;
        }
    }


    // identify all the fieldsets and check if all the required forms are filled
    var fields = document.getElementsByTagName('fieldset');
    for (var i = 0; i < fields.length; ++i) {
        var inputs = fields[i].querySelectorAll('input[validation=required], select[validation=required], textarea[validation=required]') as NodeListOf<HTMLInputElement>;

        // continue if all there's no required inputs in the current field set
        if (inputs.length == 0) {
            continue;
        }
        //var required = true;
        // check if the current form requires inputs
        //if (inputs[0].getAttribute('validation') == 'required'){
        //    required= true;
        //}


        let checked_flag = false;
        for (var j = 0; j < inputs.length; ++j) {
            // if a right_label is not selected, display an error msg and return false
            //if (inputs[j].getAttribute('validation') == 'right_label' && inputs[j].checked == false) {
            //    alert(inputs[j].name + " must be selected to proceed");
            //alert(instance_obj.id)
            //    return false;
            //}
            // if the input is for a span annotation schema, check if the at least some span is annotated or if the
            // bad_text label is selected
            if (inputs[j].getAttribute("for_span") == "True") {
                if ($(".span_container").length > 0) {
                    checked_flag = true;
                    break;
                } else if (inputs[j].name.slice(-8) == "bad_text" && inputs[j].checked == true) {
                    checked_flag = true;
                    break;
                }
            }


            // if any of the labels is checked, set checked_flag as true;
            if (inputs[j].getAttribute("for_span") != "True" && inputs[j].checked == true) {

                checked_flag = true;
                break;
            }

            // if the input_type is number, text, select or textarea, check if it's empty
            // todo: the current way might not work well if there are mixed textinput and radio buttons under a sample fieldset
            if (inputs[j].type == "text" || inputs[j].tagName == "TEXTAREA" || inputs[j].type == "number" || inputs[j].type == "select-one") {
                if (inputs[j].value.length == 0) {
                    alert(inputs[j].name + " must be completed to proceed");
                    return false;
                }
                else {
                    checked_flag = true;
                }
            }
        }


        // if this form requires inputs, but nothing is checked, display an error msg and return false
        if (checked_flag == false) {
            alert("You must answer the following item to proceed: " + inputs[0].className);
            return false;
        }
        //alert(instance_obj.id)
    }
    return true;
}
