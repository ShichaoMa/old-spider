"use strict";
var system = require("system");
var page = require('webpage').create(), loadInProgress = false, testindex=0, captcha, ImageLoaded = false;

function waitFor(testFx, onReady, timeOutMillis) {
    var maxtimeOutMillis = timeOutMillis ? timeOutMillis : 3000, //< Default Max Timout is 3s
        start = new Date().getTime(),
        condition = false,
        interval = setInterval(function() {
            if ( (new Date().getTime() - start < maxtimeOutMillis) && !condition ) {
                // If not time-out yet and condition not yet fulfilled
                condition = (typeof(testFx) === "string" ? eval(testFx) : testFx()); //< defensive code
            } else {
                if(!condition) {
                    // If condition still not fulfilled (timeout but condition is 'false')
                    console.log("'waitFor()' timeout");
                    phantom.exit(1);
                } else {
                    // Condition fulfilled (timeout and/or condition is 'true')
                    console.log("'waitFor()' finished in " + (new Date().getTime() - start) + "ms.");
                    typeof(onReady) === "string" ? eval(onReady) : onReady(); //< Do what it's supposed to do once the condition is fulfilled
                    clearInterval(interval); //< Stop this interval
                }
            }
        }, 250); //< repeat check every 250ms
}
page.clipRect = {
	top: parseInt(725) ,
	left: parseInt(28),
	width: parseInt(300),
	height: parseInt(57)};
page.settings.userAgent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36";
// page.onResourceReceived = function(response) {
//     console.log('Response (#' + response.id + ', stage "' + response.stage + '"): ' + JSON.stringify(response));
// };

page.onConsoleMessage = function(msg) {
  console.log(msg);
};

page.onLoadStarted = function() {
  loadInProgress = true;
  //console.log("load started");
};

page.onLoadFinished = function() {
  loadInProgress = false;
  //console.log("load finished");
};

// page.onResourceRequested = function(requestData, networkRequest) {
//   console.log('Request (#' + requestData.id + '): ' + JSON.stringify(requestData));
// };

var steps = [
  function() {
    page.open('https://www.jomashop.com/distil_r_captcha.html', function(status){
        waitFor(function (){
        return page.evaluate(function() {
            return document.getElementById("recaptcha_challenge_image");
            });
        }, function(){
            page.render("captcha.png");
            ImageLoaded = true;
            system.stdout.write('enter captcha: ');
            captcha = system.stdin.readLine();
            //console.log("recv captcha: ", captcha);
            var cookies = page.cookies;
        }, 10000);
    });
  },
  function() {
    page.evaluate(function (captcha) {
        var form = document.getElementById("distilCaptchaForm");
        form.elements[2].value = captcha;
        form.submit();
        return document.title;
    }, captcha);
  },
  function() {
    var cookies = page.cookies;
    //console.log('Listing cookies:',cookies.length);
    var cs = "";
    if (cookies.length >10){
        for(var i in cookies) {
            if(cookies[i].domain.indexOf("jomashop.com") != -1 && cookies[i].path == "/"){
               cs += cookies[i].name + '=' + cookies[i].value + ";";
            }
        }
    }
    console.log("Cookies is: ", cs);
  }
];

setInterval(function() {
    if (!loadInProgress){
        if (typeof steps[testindex] == "function"){
            if(testindex == 1 && !ImageLoaded){
                return
            }
            console.log("step " + (testindex + 1));
            steps[testindex]();
            testindex++;
        }else{
            console.log("test complete!", testindex, steps[testindex]);
            phantom.exit();
        }
    }
}, 1000);


