/* Set the width of the sidebar to 250px (show it) */
function openNav(target_id, width = "350px") {
    document.getElementById(target_id).style.width = width;
}

/* Set the width of the sidebar to 0 (hide it) */
function closeNav(target_id) {
    document.getElementById(target_id).style.width = "0";
}

function closeNav2(target_id) {
    // document.getElementById(target_id).style.height = "20px";
    console.error(document.getElementById(target_id).style.display);
    if (document.getElementById(target_id).style.display == "block" 
        || document.getElementById(target_id).style.display == "") {
        
        document.getElementById(target_id).style.display = "none";
        localStorage.setItem('show_instructions', 'false'); 
    }
    else{
        document.getElementById(target_id).style.display = "block";
        localStorage.setItem('show_instructions', 'true'); 
    }
}

/* Keep the instructions hidden/shown across instance transitions based on
   what the user had selected */      
window.onload = function() {
    var show = localStorage.getItem('show_instructions');
    if (document.getElementById('instructions')) {
        if (show === 'true') {
            document.getElementById('instructions').style.display = "block";
        }
        else {
            document.getElementById('instructions').style.display = "none";
        }
    }
}   