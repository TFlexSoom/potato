document.addEventListener('keyup', function (event) {
    var active_id = document.activeElement.id;
    var active_type = document.activeElement.getAttribute('type');
    if (active_id == 'go_to' | active_type == 'text') return;

    //first check whether this keyboard input is a shortcut for checkboxes
    var checkboxes = document.querySelectorAll('input[type=checkbox]');
    var radios = document.querySelectorAll('input[type=radio]');
    var x = event.key.toLowerCase();

    for (var i = 0; i < checkboxes.length; i++) {
        //alert(checkboxes[i].value)
        if(x === checkboxes[i].value){
            checkboxes[i].checked = !checkboxes[i].checked;
            if (checkboxes[i].onclick != null) checkboxes[i].onclick.apply(checkboxes[i]);
            return;
        };
    }
    for (var i = 0; i < radios.length; i++) {
        //alert(checkboxes[i].value)
        if(x === radios[i].value){
            radios[i].checked = !radios[i].checked;
            if (radios[i].onclick != null) radios[i].onclick.apply(radios[i]);
            return;
        };
    }

    // Each time we process a user's key presses, track who is doing
    // it by grabbing the hidden firstname and lastname fields
    get_new_instance(event);          
});

function click_to_next() {
    // Gacky code to simulate the submit button as a keyboard event
    // and not have two separate paths to handle keyboard and mouse
    // events
    var e = $.Event('keyup');
    e.key = "ArrowRight";
    
    get_new_instance(e);
}

function click_to_prev() {
    // Gacky code to simulate the submit button as a keyboard event
    // and not have two separate paths to handle keyboard and mouse
    // events
    var e = $.Event('keyup');
    e.key = "ArrowLeft";
    
    get_new_instance(e);
}
