
import { createHash } from "node:crypto";
import { getElementById } from "./document";

function sha256(str: string) {
    return createHash('sha256').update(str).digest("hex");
}

function getInputValue(id: string): any {
    const elem = getElementById(id);
    if(!elem) {
        throw Error(`No Element with id ${id}`);
    }

    return (elem as HTMLInputElement).value;
}


export function login() {
    if (check_input_fields("login") == false) {
        return false;
    }
    var email = getInputValue('login_email');
    var password = sha256(getInputValue('login_pass'));


    // Sends the post message to the server which will let us update the
    // currently displayed content
    // The rest of this code assumes you are not using a library.
    // It can be made less wordy if you use one.
    var form = document.createElement("form");
    form.setAttribute("method", "post");
    form.setAttribute("action", "login");

    var hiddenField = document.createElement("input");
    hiddenField.setAttribute("type", "hidden");
    hiddenField.setAttribute("name", "src");
    hiddenField.setAttribute("value", "home");
    form.appendChild(hiddenField);

    var hiddenField = document.createElement("input");
    hiddenField.setAttribute("type", "hidden");
    hiddenField.setAttribute("name", "action");
    hiddenField.setAttribute("value", "login");
    form.appendChild(hiddenField);

    hiddenField = document.createElement("input");
    hiddenField.setAttribute("type", "hidden");
    hiddenField.setAttribute("name", "email");
    hiddenField.setAttribute("value", email);
    form.appendChild(hiddenField);

    hiddenField = document.createElement("input");
    hiddenField.setAttribute("type", "hidden");
    hiddenField.setAttribute("name", "pass");
    hiddenField.setAttribute("value", password);
    form.appendChild(hiddenField);

    document.body.appendChild(form);
    form.submit();
}

export function signup() {
    if (check_input_fields("signup") == false) {
        return false;
    }
    var email = getInputValue('login_email');
    var password = sha256(getInputValue('login_pass'));

    // Sends the post message to the server which will let us update the
    // currently displayed content
    // The rest of this code assumes you are not using a library.
    // It can be made less wordy if you use one.
    var form = document.createElement("form");
    form.setAttribute("method", "post");
    form.setAttribute("action", "signup");

    var hiddenField = document.createElement("input");
    hiddenField.setAttribute("type", "hidden");
    hiddenField.setAttribute("name", "action");
    hiddenField.setAttribute("value", "signup");
    form.appendChild(hiddenField);

    hiddenField = document.createElement("input");
    hiddenField.setAttribute("type", "hidden");
    hiddenField.setAttribute("name", "email");
    hiddenField.setAttribute("value", email);
    form.appendChild(hiddenField);

    hiddenField = document.createElement("input");
    hiddenField.setAttribute("type", "hidden");
    hiddenField.setAttribute("name", "pass");
    hiddenField.setAttribute("value", password);
    form.appendChild(hiddenField);

    document.body.appendChild(form);
    form.submit();
}

// check all input fields
function check_input_fields(action: string) {
    if (validateEmail(getInputValue(action + '_email'), action) == false) {
        (document.getElementById(action + '_error') as HTMLElement).innerHTML = "Invalid email address";
        return false;
    } else if (validatePassword(getInputValue(action + '_pass'), action) == false) {
        //getInputValue('signup_error').innerHTML = "Invalid email address";
        return false;
    } else if (confirmPassword(action) == false) {
        return false;
    }
    return true;
}

// check email for registration
function validateEmail(email: string, action: string) {
    var msg_key = action + "_error";
    if (/^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/.test(email)) {
        (document.getElementById(msg_key) as HTMLElement).innerHTML = "";
        return true;
    }
    else {
        (document.getElementById(msg_key) as HTMLElement).innerHTML = "Invalid email address";
        return false;
    }
}

// check password for registration
function validatePassword(password: string, action: string) {
    var pw = password;
    var msg_key = action + "_error";
    //check empty password field
    if (pw == "") {
        (document.getElementById(msg_key) as HTMLElement).innerHTML = "Password cannot be empty";
        return false;
    }

    //minimum password length validation
    if (pw.length < 6) {
        (document.getElementById(msg_key) as HTMLElement).innerHTML = "Password length must be at least 6 characters";
        return false;
    }

    //maximum length of password validation
    if (pw.length > 15) {
        (document.getElementById(msg_key) as HTMLElement).innerHTML = "Password length must not exceed 15 characters";
        return false;
    }

    (document.getElementById(msg_key) as HTMLElement).innerHTML = "";
    return true;
}

// check confirmation password
function confirmPassword(action: string) {
    if (action == "signup") {
        var msg_key = action + "_error";
        var pw1 = getInputValue("signup_pass");
        var pw2 = getInputValue("pass_again");
        if (pw1 != pw2) {
            (document.getElementById(msg_key) as HTMLElement).innerHTML = "Password not match";
            return false;
        }
        (document.getElementById(msg_key) as HTMLElement).innerHTML = "";
        return true;
    }
}