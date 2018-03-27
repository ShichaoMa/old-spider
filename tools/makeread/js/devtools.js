// 创建自定义面板，同一个插件可以创建多个自定义面板
// 几个参数依次为：panel标题、图标（其实设置了也没地方显示）、要加载的页面、加载成功后的回调
chrome.devtools.panels.create('MyPanel', '', 'mypanel.html', function(panel)
{
    console.log('自定义面板创建成功！'); // 注意这个log一般看不到
});

// 创建自定义侧边栏
chrome.devtools.panels.elements.createSidebarPane("Images", function(sidebar)
{
    // sidebar.setPage('../sidebar.html'); // 指定加载某个页面
    sidebar.setExpression('document.querySelectorAll("img")', 'All Images'); // 通过表达式来指定
    //sidebar.setObject({aaa: 111, bbb: 'Hello World!'}); // 直接设置显示某个对象
});

// 检测jQuery
document.getElementById('check_jquery').addEventListener('click', function()
{
    // 访问被检查的页面DOM需要使用inspectedWindow
    // 简单例子：检测被检查页面是否使用了jQuery
    chrome.devtools.inspectedWindow.eval("jQuery.fn.jquery", function(result, isException)
    {
        var html = '';
        if (isException) html = '当前页面没有使用jQuery。';
        else html = '当前页面使用了jQuery，版本为：'+result;
        alert(html);
    });
});

// 打开某个资源
document.getElementById('open_resource').addEventListener('click', function()
{
    chrome.devtools.inspectedWindow.eval("window.location.href", function(result, isException)
    {
        chrome.devtools.panels.openResource(result, 20, function()
        {
            console.log('资源打开成功！');
        });
    });
});

// 审查元素
document.getElementById('test_inspect').addEventListener('click', function()
{
    chrome.devtools.inspectedWindow.eval("inspect(document.images[0])", function(result, isException){});
});

// 获取所有资源
document.getElementById('get_all_resources').addEventListener('click', function()
{
    chrome.devtools.inspectedWindow.getResources(function(resources)
    {
        alert(JSON.stringify(resources));
    });
});