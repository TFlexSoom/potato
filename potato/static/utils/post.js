window.onunload = check_close;
function check_close() {
    // console.error("session closed");
    var post_req = {
        is_close: "closed"
    }
    post(post_req);
}

 // We submit a new post to the same (user/annotate) endpoint
 function post(params) {
          
    // The rest of this code assumes you are not using a library.
    // It can be made less wordy if you use one.
    var form = document.createElement("form");
    form.setAttribute("method", "post");
    form.setAttribute("action", "annotate");
    
    var hiddenField = document.createElement("input");
    hiddenField.setAttribute("type", "hidden");
    hiddenField.setAttribute("name", "email");
    hiddenField.setAttribute("value", document.getElementById('username').value);
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
    $('form input, form select, form textarea').each(
        function(index){  
            var input = $(this);
            
            if (input.attr('type') == 'checkbox' || input.attr('type') == 'radio') {
                if (input.is(":checked")) {
                    // Stuff all the input fields into something for the post
                    var hiddenField = document.createElement("input");
                    hiddenField.setAttribute("type", "hidden");
                    hiddenField.setAttribute("name", input.attr('name'));
                    hiddenField.setAttribute("value", input.attr('value'));
                    form.appendChild(hiddenField);
                }
            }
            else if (input.attr('type') == 'text' || input.attr('type') == 'number') {
                var hiddenField = document.createElement("input");
                hiddenField.setAttribute("type", "hidden");
                hiddenField.setAttribute("name", input.attr('name'));
                hiddenField.setAttribute("value", input[0].value);
                form.appendChild(hiddenField);                                        
            }
            else if (input.attr('type') == 'range') {
                var hiddenField = document.createElement("input");
                hiddenField.setAttribute("type", "hidden");
                hiddenField.setAttribute("name", input.attr('name'));
                hiddenField.setAttribute("value", input[0].value);
                form.appendChild(hiddenField);                                        
            }
            else if (input.attr('type') == 'select-one') {
                //alert(input[0].value)
                var hiddenField = document.createElement("input");
                hiddenField.setAttribute("type", "hidden");
                hiddenField.setAttribute("name", input.attr('name'));
                hiddenField.setAttribute("value", input[0].value);
                form.appendChild(hiddenField);
            }
            else {
                console.log("unknown form type: \"" + input.attr('type') + "\"")
            }
        }
    );

    // Get all the highlighted text for this instance and marshall that
    // into some kind of representation for the server side
    $(".span_container").first().each(
        function(index) {

            // we save the outerHTML to accomadate user-defined HTML inputs,
            // otherwise we just save the plain text
            if ($(this).parent().parent().attr("name") == "instance_text"){
                var annotated_spans = $(this).parent().prop('outerHTML');
            } else {
                var annotated_spans = $(this).parent().prop('innerHTML');
            }

            // Due to the DJ's inability to write decent Javascript, we're
            // fully punting on the idea of doing label preprocessing here
            // and instead shuttling the entire HTML of the instance to
            // the server for python-based processing. The main issue is
            // figuring out the precise text offsets of the annotated
            // spans while dealing with nested DOM elements.
            var hiddenField = document.createElement("input");
            hiddenField.setAttribute("type", "hidden");
            hiddenField.setAttribute("name", "span-annotation");
            hiddenField.setAttribute("value", annotated_spans);
            form.appendChild(hiddenField);
            //console.log(annotated_spans)
        }
    );

    
    document.body.appendChild(form);
    form.submit();
}

/**
 * Validate if the user has completed each row for multi-rate schema
 */
function validateForm() {
  var rows = document.querySelectorAll("tr[schema='multirate']");
  for (var i = 0; i < rows.length; i++) {
    var inputs = rows[i].querySelectorAll("input[type='radio'][validation='required']");
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
    var inputs =  document.querySelectorAll('input[validation=right_label]');
    for (var i = 0; i < inputs.length; ++i) {
      if (inputs[i].getAttribute('validation') == 'right_label' && inputs[i].checked == false){
          alert(inputs[i].name + " must be selected to proceed");
          //alert(instance_obj.id)
          return false;
      }
    }


    // identify all the fieldsets and check if all the required forms are filled
    var fields = document.getElementsByTagName('fieldset');
    for (var i = 0; i < fields.length; ++i) {
          var inputs = fields[i].querySelectorAll('input[validation=required], select[validation=required], textarea[validation=required]');

          // continue if all there's no required inputs in the current field set
          if (inputs.length == 0){
              continue;
          }
          //var required = true;
          // check if the current form requires inputs
          //if (inputs[0].getAttribute('validation') == 'required'){
          //    required= true;
          //}


          checked_flag = false;
          for (var j = 0; j < inputs.length; ++j) {
              // if a right_label is not selected, display an error msg and return false
              //if (inputs[j].getAttribute('validation') == 'right_label' && inputs[j].checked == false) {
              //    alert(inputs[j].name + " must be selected to proceed");
                  //alert(instance_obj.id)
              //    return false;
              //}
              // if the input is for a span annotation schema, check if the at least some span is annotated or if the
              // bad_text label is selected
              if (inputs[j].getAttribute("for_span") == "True"){
                  //alert($(".span_container").length);
                  if ($(".span_container").length > 0) {
                      checked_flag = true;
                      break;
                  } else if (inputs[j].name.slice(-8) == "bad_text" && inputs[j].checked == true){
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
                  if (inputs[j].value.length == 0){
                      alert(inputs[j].name + " must be completed to proceed");
                      return false;
                  }
                  else{
                      checked_flag = true;
                  }
              }
          }


          // if this form requires inputs, but nothing is checked, display an error msg and return false
          if (checked_flag == false){
              alert("You must answer the following item to proceed: " + inputs[0].className);
              return false;
          }
          //alert(instance_obj.id)
    }
    return true;
}


/**
 * Sends the current state of the instance's annotation to the server,
 * along with any relevant key presses to request a new instance to
 * annotate.
 */
function get_new_instance(event) {
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
        else{
            return;
        }
    }
    else {
        // console.log("Unknown key press", event)
        return
    }
    
    var instance_id = document.getElementById('instance_id').value
    var time_string = document.getElementById("timecounter").innerHTML //get time spent on this instance
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