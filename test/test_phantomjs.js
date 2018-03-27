var page = require('webpage').create();
page.settings.userAgent =  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"

page.onResourceRequested = function (req) {
	if(req.url.indexOf("offer-listing") != -1){
	        console.log('requested: ' + JSON.stringify(req, undefined, 4));	
	    }
};

page.onResourceReceived = function (res) {
	if (res.url.indexOf("offer-listing") != -1){
		        console.log('received: ' + JSON.stringify(res, undefined, 4));
	}
};

page.open('https://www.amazon.com/gp/offer-listing/B01NCILWOU/ref=dp_olp_0?ie=UTF8&condition=all', function(status) {
  console.log("Status: " + status);
  if(status === "success") {
    page.render('example.png');
  }
  phantom.exit();
});