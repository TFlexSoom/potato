/* Set the width of the sidebar to 250px (show it) */
export function openNav(target_id: string, width = "350px") {
    const target = document.getElementById(target_id);
    if (target === null) {
        return;
    }

    target.style.width = width;
}

/* Set the width of the sidebar to 0 (hide it) */
export function closeNav(target_id: string) {
    const target = document.getElementById(target_id);
    if (target === null) {
        return;
    }
    
    target.style.width = "0";
}

export function closeNav2(target_id: string) {
    const target = document.getElementById(target_id);
    if (target === null) {
        return;
    }
    
    // document.getElementById(target_id).style.height = "20px";
    console.error(target.style.display);
    if (target.style.display == "block" || target.style.display == "") {
        target.style.display = "none";
        localStorage.setItem('show_instructions', 'false'); 
    }
    else{
        target.style.display = "block";
        localStorage.setItem('show_instructions', 'true'); 
    }
}

/* Keep the instructions hidden/shown across instance transitions based on
   what the user had selected */      
// window.onload = function() {
export function showInstructions() {
    const instructions = document.getElementById('instructions');
    if(instructions === null) {
        return;
    }
    
    var show = localStorage.getItem('show_instructions');
    if (show === 'true') {
        instructions.style.display = "block";
    }
    else {
        instructions.style.display = "none";
    }
}   