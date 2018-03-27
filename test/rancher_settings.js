function fun(name){
    let ele = $('#' + name + ' table tr td');
    for(let i=0; i<ele.length; i+=4){
        console.log($(ele[i]).find("input").val(), "=", $(ele[i+2]).find("textarea").val());
    }
}