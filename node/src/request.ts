/*
 * author: Tristan Hilbert
 * date: 10/4/2024
 * filename: request.js
 * desc: Temporary web request function
 */

// Might want to switch this to axios or something more standard
export function postJson(url: URL, parcel: any) {
    return new Promise(function(resolve, reject) {
        var xhr = new XMLHttpRequest();
        xhr.onreadystatechange = function() {
            if(xhr.readyState === XMLHttpRequest.DONE && xhr.status === 200) {
                resolve(xhr.response);
            } else if (xhr.readyState === XMLHttpRequest.DONE) {
                reject("invalid status " + xhr.status);
            }
        };
        xhr.open("POST", url);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.send(parcel);
    });
}