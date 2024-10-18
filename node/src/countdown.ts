// Set the date we're counting down t
const countDownDate = new Date().getTime();

// Update the count down every 1 second
// export const x = setInterval(
export function triggerTime() {

    // Get today's date and time
    const now = new Date().getTime();

    // Find the distance between now and the count down date
    const distance = now - countDownDate;

    // Time calculations for days, hours, minutes and seconds
    const days = Math.floor(distance / (1000 * 60 * 60 * 24));
    const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((distance % (1000 * 60)) / 1000);
    const total_seconds = Math.floor(distance / 1000);

    // Output the result in an element with id="timecounter"
    const timeCounterElem = document.getElementById("timecounter");
    if(timeCounterElem === null) {
        console.error("no time counter element!");
        return;
    }

    (timeCounterElem as HTMLElement).innerHTML = "Time spent: " + days + "d " + hours + "h "
        + minutes + "m " + seconds + "s ";

    // TODO: add configurations for alert message and maximum time spent on each instance
    // If the count down is over, write some text
    const alertTimeElement = document.getElementById("alert_time_each_instance") as HTMLInputElement;
    if(alertTimeElement === null) {
        console.error("no alert element!");
        return;
    }
    
    const alert_time_each_instance = Number.parseInt(alertTimeElement.value);
    if (total_seconds % alert_time_each_instance == 0) {
        //clearInterval(x);
        //document.getElementById("timecounter").innerHTML = "EXPIRED";
        alert("You have spent " + total_seconds + " seconds on this instance")
    }

}
