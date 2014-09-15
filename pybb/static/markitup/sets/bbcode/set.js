// ----------------------------------------------------------------------------
// markItUp!
// ----------------------------------------------------------------------------
// Copyright (C) 2011 Jay Salvat
// <a href="http://markitup.jaysalvat.com/" target="_blank">markitup.jaysalvat.com/</a>
// ----------------------------------------------------------------------------
// Html tags
// <a href="http://en.wikipedia.org/wiki/html" target="_blank">en.wikipedia.org/wiki/html</a>
// ----------------------------------------------------------------------------
// Basic set. Feel free to add more tags
// ----------------------------------------------------------------------------
var mySettings = {
    onEnter:    {keepDefault:false, replaceWith:'\n'},
    onShiftEnter:   {keepDefault:false, openWith:'n<p>', closeWith:'</p>'},
    onCtrlEnter:    {keepDefault:false, replaceWith: ''},
    onTab:          {keepDefault:false, replaceWith:'   '},
    resizeHandle: true,
    previewAutoRefresh: true,
    markupSet:  [  
        {name: 'Text Sizes and Headings', className: 'Heading',
            dropMenu: [
                {name:'<h1>Heading</h1>', className: 'Heading1', key:'1', openWith:'<h1>', closeWith:'</h1>', placeHolder:'Your title here...' },
                {name:'<h2>Heading 2</h2>', className: 'Heading2', key:'2', openWith:'<h2>', closeWith:'</h2>', placeHolder:'Your title here...' },
                {name:'<h3>Heading 3</h3>', className: 'Heading3', key:'3', openWith:'<h3>', closeWith:'</h3>', placeHolder:'Your title here...' },
                {name:'<h4>Heading 4</h4>', className: 'Headin4', key:'4', openWith:'<h4>', closeWith:'</h4>', placeHolder:'Your title here...' },
                {name:'<h5>Heading 5</h5>', className: 'Heading5', key:'5', openWith:'<h5>', closeWith:'</h5>', placeHolder:'Your title here...' },
                {name:'<h6>Heading 6</h6>', className: 'Heading6', key:'6', openWith:'<h6>', closeWith:'</h6>', placeHolder:'Your title here...' },
            ]
        },
        {name: 'Align Text', className: 'mAlign',
            dropMenu: [
                {name: 'Cente', className: 'mCenter', openWith: '<p style="text-align: center;">', closeWith: '</p>'},
                {name: 'Justify', className: 'mJustify', openWith: '<p style="text-align: jusity;">', closeWith: '</p>'},
                {name: 'Left', className: 'mLeft', openWith: '<p style="text-align: left;">', closeWith: '</p>'},
                {name: 'Right', className: 'mRight', openWith: '<p style="text-align: rright;">', closeWith: '</p>'}
            ]
        },
        {name:'Horizonal Line', className: 'pHr', openWith:'<hr>' },
        {name:'Paragraph', className: 'pTag', openWith:'<p>', closeWith:'</p>' },
        {name:'Quote', className: 'pQuote', openWith:'<blockquote>', closeWith:'</blockquote>' },
        {name:'Read More/cut off page', className: 'pPagebreak', openWith:'' },
        {separator:'---------------' },
        {name:'Bold', key:'B', className: 'pBold', openWith:'<strong>', closeWith:'</strong>' },
        {name:'Italic', key:'I', className: 'pItalic', openWith:'<em>', closeWith:'</em>'  },
        {name:'Strike through', className: 'pStrike', key:'S', openWith:'<del>', closeWith:'</del>' },
        {name:'Underline', className: 'pUnderline', key:'U', openWith:'<span style="text-decoration:underline">', closeWith:'</span>' },
        {name: 'Font Family', className: 'pFontFamily', dropMenu: [
            {name: '<span style="font-family:Comic Sans MS">Comic Sans MS</span>', openWith:'<span style="font-family:Comic Sans MS">', closeWith:'</span>'},
            {name: '<span style="font-family:Georgia">Georgia</span>', openWith:'<span style="font-family:Georgia">', closeWith:'</span>'},
            {name: '<span style="font-family:Times New Roman">Times New Roman</span>', openWith:'<span style="font-family:Times New Roman">', closeWith:'</span>'},
            {name: '<span style="font-family:Palatino">Palatino</span>', openWith:'<span style="font-family:Palatino">', closeWith:'</span>'},
            {name: '<span style="font-family:Garamond">Garamond</span>', openWith:'<span style="font-family:Garamond">', closeWith:'</span>'},
            {name: '<span style="font-family:Bookman">Bookman</span>', openWith:'<span style="font-family:Bookman">', closeWith:'</span>'},
            {name: '<span style="font-family:Verdana">Verdana</span>', openWith:'<span style="font-family:Verdana">', closeWith:'</span>'},
            {name: '<span style="font-family:Impact">Impact</span>', openWith:'<span style="font-family:Impact">', closeWith:'</span>'},
            {name: '<span style="font-family:Papyrus">Papyrus</span>', openWith:'<span style="font-family:Papyrus">', closeWith:'</span>'},
            {name: '<span style="font-family:Avant Garde">Avant Garde</span>', openWith:'<span style="font-family:Avant Garde">', closeWith:'</span>' }
        ]},
        {name: 'Font Color', className:'palette', dropMenu: [
            {name: 'yellow',    openWith:'<span style="color:#FCE94F;">', closeWith: '</span>', className:"col1-1" },
            {name: 'yellow',    openWith:'<span style="color:#EDD400;">', closeWith: '</span>',     className:"col1-2" },
            {name: 'yellow',    openWith:'<span style="color:#C4A000;">', closeWith: '</span>',     className:"col1-3" },
 
            {name: 'orange',    openWith:'<span style="color:#FCAF3E;">', closeWith: '</span>',     className:"col2-1" },
            {name: 'orange',    openWith:'<span style="color:#F57900;">', closeWith: '</span>',     className:"col2-2" },
            {name: 'orange',    openWith:'<span style="color:#CE5C00;">', closeWith: '</span>',     className:"col2-3" },
 
            {name: 'brown',     openWith:'<span style="color:#E9B96E;">', closeWith: '</span>',     className:"col3-1" },
            {name: 'brown',     openWith:'<span style="color:#C17D11;">', closeWith: '</span>',     className:"col3-2" },
            {name: 'brown',     openWith:'<span style="color:#8F5902;">', closeWith: '</span>', className:"col3-3" },
 
            {name: 'green',     openWith:'<span style="color:#8AE234;">', closeWith: '</span>',     className:"col4-1" },
            {name: 'green',     openWith:'<span style="color:#73D216;">', closeWith: '</span>', className:"col4-2" },
            {name: 'green',     openWith:'<span style="color:#4E9A06;">', closeWith: '</span>', className:"col4-3" },
 
            {name: 'blue',      openWith:'<span style="color:#729FCF;">', closeWith: '</span>', className:"col5-1" },
            {name: 'blue',      openWith:'<span style="color:#3465A4;">', closeWith: '</span>', className:"col5-2" },
            {name: 'blue',      openWith:'<span style="color:#204A87;">', closeWith: '</span>', className:"col5-3" },
 
            {name: 'purple',    openWith:'<span style="color:#AD7FA8;">', closeWith: '</span>', className:"col6-1" },
            {name: 'purple',    openWith:'<span style="color:#75507B;">', closeWith: '</span>', className:"col6-2" },
            {name: 'purple',    openWith:'<span style="color:#5C3566;">', closeWith: '</span>', className:"col6-3" },
 
            {name: 'red',       openWith:'<span style="color:#EF2929;">', closeWith: '</span>', className:"col7-1" },
            {name: 'red',       openWith:'<span style="color:#CC0000;">', closeWith: '</span>', className:"col7-2" },
            {name: 'red',       openWith:'<span style="color:#A40000;">', closeWith: '</span>', className:"col7-3" },
 
            {name: 'gray',      openWith:'<span style="color:#FFFFFF;">', closeWith: '</span>', className:"col8-1" },
            {name: 'gray',      openWith:'<span style="color:#D3D7CF;">', closeWith: '</span>', className:"col8-2" },
            {name: 'gray',      openWith:'<span style="color:#BABDB6;">', closeWith: '</span>', className:"col8-3" },
 
            {name: 'gray',      openWith:'<span style="color:#888A85;">', closeWith: '</span>', className:"col9-1" },
            {name: 'gray',      openWith:'<span style="color:#555753;">', closeWith: '</span>', className:"col9-2" },
            {name: 'gray',      openWith:'<span style="color:#000000;">', closeWith: '</span>', className:"col9-3" }
        ]},
        {separator:'---------------' },
        {name:'Ul', className: 'listU', openWith:'<ul>n<li>', closeWith:'</li>n</ul>n', placeHolder:'' },
        {name:'Ol', className: 'listO', openWith:'<ol>n<li>', closeWith:'</li>n</ol>n', placeHolder:'' },
        {name:'Li', className: 'listL', openWith:'<li>', closeWith:'</li>' },
        {separator:'---------------' },
        {name: 'My Gallery Files', className: 'GalPic', beforeInsert:function() {
                $('<iframe src="../../../themes/admin/Admin.Pictures.Popup4Posting.php" width="790" height="490"></iframe>').modal(
                    {overlayClose:true, autoResize:true, minHeight:500, minWidth:800, onOpen: function (dialog) {
                        dialog.overlay.fadeIn('slow', function () {
                            dialog.container.slideDown('slow', function () {
                                dialog.data.fadeIn('slow');
                            });
                        });
                    }});
            }
        },
        {name:'Picture', className:'PicTag', dropMenu: [
            {name: 'Image Left', className: 'pImgLeft', replaceWith:'<img src="[![Source:!:<a href=" http:="" ]!]"="" target="_blank">]!]" alt="[![Alternative text]!]" style="float:left; padding:5px;" />' },
            {name: 'Centered Image', className: 'pImgCenter', replaceWith:'<p style="text-align:center;"><img src="[![Source:!:<a href=" http:="" ]!]"="" target="_blank">]!]" alt="[![Alternative text]!]" /></p>' },
            {name: 'Image Right', className: 'pImgRight', replaceWith:'<img src="[![Source:!:<a href=" http:="" ]!]"="" target="_blank">]!]" alt="[![Alternative text]!]" style="float:right; padding:5px;" />' }
        ]},
        {name:'Link', className: 'LinkTag', key:'L', openWith:'<a href="[![Link:!:<a href=" http:="" ]!]"="" target="_blank">]!]</a>"(!( title="[![Title]!]")!)>[![Link Name]!]', closeWith:'' }, // , placeHolder:'Your text to link...'
        { name:'Insert You Tube Video', className: 'youtube', replaceWith: function(mark){
                var nameYT = prompt('Enter You Tube URL', 'http://');
                if (nameYT != null && nameYT != "" && nameYT != 'http://'){
                    var YTUrl = nameYT.replace('http://www.youtube.com/watch?v=', '');
                    $.markItUp( { replaceWith: '<object width="425" height="350"><param name="movie" value="http://www.youtube.com/v/'+YTUrl+'"><embed src="http://www.youtube.com/v/'+YTUrl+'" type="application/x-shockwave-flash" autostart="1" allowscriptaccess="never" wmode="transparent" width="425" height="350"></object>' } );
                } else { return false; }
            }
        },
        { name:'Insert Google Map', className: 'pMaps', replaceWith: function(mark){
            var address = prompt('Address:', '');
            if(address != null && address != ''){
                var addr = address.replace(/s/g, '+');
                $.markItUp( { replaceWith: '<a alt="map" href="http://maps.google.com/maps?f=q&source=s_q&hl=en&geocode=&q='+addr+'&z=16"><img alt="map" src="http://maps.google.com/maps/api/staticmap?center='+addr+'&zoom=15&size=400x400&maptype=roadmap&markers=color:red|'+addr+'&sensor=false"></a>' } );
            } else { return false; }
        }
        },
        {separator:'---------------' },
        {   name:'Sort',   
            className:"sort",
            replaceWith:function(h) {
                var s = h.selection.split((($.browser.mozilla) ? "n" : "rn"));
                s.sort();
                if (h.altKey) s.reverse();
                return s.join("n");
            }
        },
        {   name:'Encode Html special charsn make ready for display',
            className:"encodechars",
            replaceWith:function(markItUp) {
                var container = document.createElement('div');
                container.appendChild(document.createTextNode(markItUp.selection));
                return container.innerHTML;
            }
        },
        {name:'Code', className: 'pCode', dropMenu: [
            {name: 'PHP', className: 'Cphp', openWith:'<pre class="brush: php">', closeWith: '</pre>' },
            {name: 'CSS', className: 'Ccss', openWith:'<pre class="brush: css">', closeWith: '</pre>' },
            {name: 'JavaScript', className: 'Cjs', openWith:'<pre class="brush: js">', closeWith: '</pre>' },
            {name: 'SQL', className: 'Csql', openWith:'<pre class="brush: sql">', closeWith: '</pre>' },
            {name: 'HTML', className: 'Chtml', openWith:'<pre class="brush: html">', closeWith: '</pre>' },
            {name: 'XML', className: 'Cxml', openWith:'<pre class="brush: xml">', closeWith: '</pre>' },
            {name: 'Plain', className: 'Cplain', openWith:'<pre class="brush: plain">', closeWith: '</pre>' }
        ]},
        {name:'Erase Coding', className:'clean', replaceWith:function(markitup) { return markitup.selection.replace(/<(.*?)>/g, "") } },     
        {name:'Preview', className:'preview',  call:'preview'}
    ]
}