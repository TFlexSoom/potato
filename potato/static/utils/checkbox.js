function onlyOne(checkbox) {
    // this function is used for the single-choice setting
    //alert(checkbox.className)
    var x = document.getElementsByClassName(checkbox.className);
    var i;
    for (i = 0; i < x.length; i++) {
        if(x[i].value != checkbox.value) x[i].checked = false;
    }
}

function whetherNone(checkbox) {
    // this function is used to uncheck all the other labels when "None" is checked
    //alert(checkbox.className)
    var x = document.getElementsByClassName(checkbox.className);
    var i;
    for (i = 0; i < x.length; i++) {
        if(checkbox.value == "None" && x[i].value != "None") x[i].checked = false;
        if(checkbox.value != "None" && x[i].value == "None") x[i].checked = false;
    }

}