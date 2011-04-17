window.addEvent('domready', function() {
    HtmlTable.Parsers.sortname = {
        match: /.+/,
        convert: function() {
            return $(this).get('data-sortname');
        }
    };
    HtmlTable.Parsers.mfdate = {
        match: /.+/,
        convert: function() {
            if ($(this).getElement('span.not-applicable')) {
                return new Date()
            }
            return Date.parse($(this).getElement('time').get('datetime'));
        }
    };
    HtmlTable.Parsers.size = {
        match: /^\d+ \w?B$/,
        convert: function() {
            if ($(this).getElement('span.not-applicable')) {
                return '-2';
            }
            return $(this).getElement('span').get('title').toInt();
        },
        number: true
    };
    $$('table.list').each(function (item, index) {
        new HtmlTable(item, {sortable: true, parsers: ['sortname', 'mfdate', 'size']})
    });
});
