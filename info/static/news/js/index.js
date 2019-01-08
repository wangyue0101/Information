var currentCid = 1; // 当前分类 id
var cur_page = 1; // 当前页
var total_page = 1;  // 总页数
var house_data_querying = true;   // 是否正在向后台获取数据


$(function () {
    // 首次加载，调用获取新闻数据的函数
    updateNewsData();
    // 首页分类切换
    $('.menu li').click(function () {
        var clickCid = $(this).attr('data-cid')
        $('.menu li').each(function () {
            $(this).removeClass('active')
        })
        $(this).addClass('active')
        if (clickCid != currentCid) {
            // 记录当前分类id
            currentCid = clickCid

            // 重置分页参数
            cur_page = 1
            total_page = 1
            updateNewsData()
        }
    })

    //页面滚动加载相关
    $(window).scroll(function () {

        // 浏览器窗口高度
        var showHeight = $(window).height();

        // 整个网页的高度
        var pageHeight = $(document).height();

        // 页面可以滚动的距离
        var canScrollHeight = pageHeight - showHeight;

        // 页面滚动了多少,这个是随着页面滚动实时变化的
        var nowScroll = $(document).scrollTop();

        if ((canScrollHeight - nowScroll) < 100) {
            // 判断页数，去更新新闻数据
            if (!house_data_querying){
                // 将‘是否向后端查询数据’设为真
                //house_data_querying = true;
                // 如果当前页数还没有到达总页数，
                if (cur_page < total_page){
                    // 向后端请求下一页数据
                    updateNewsData()
                }else{
                    house_data_querying = false;
                }
            }
        }
    })
})

function updateNewsData() {
    var params = {
        "page": cur_page,
        "cid": currentCid,
        'per_page': 10
    }
    $.get("/news_list", params, function (resp) {
        // 只要发起请求，修改请求状态为false
        house_data_querying = false;
        if (resp) {
            if (cur_page == 1){
                // 先清空原有数据
            $(".list_con").html('')
            }

            total_page = resp.data.total_pages;
            cur_page += 1;

            // 显示数据
            for (var i=0;i<resp.data.news_info.length;i++) {
                var news = resp.data.news_info[i]
                var content = '<li>'
                content += '<a href="/news/'+ news.id + '" class="news_pic fl"><img src="' + news.index_image_url + '?imageView2/1/w/170/h/170"></a>'
                content += '<a href="/news/'+ news.id + '" class="news_title fl">' + news.title + '</a>'
                content += '<a href="/news/'+ news.id + '" class="news_detail fl">' + news.digest + '</a>'
                content += '<div class="author_info fl">'
                content += '<div class="source fl">来源：' + news.source + '</div>'
                content += '<div class="time fl">' + news.create_time + '</div>'
                content += '</div>'
                content += '</li>'
                $(".list_con").append(content)
            }
        }
    })
}
