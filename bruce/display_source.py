
class DisplaySource(object):
    '''Simple little listener that displays the source of the current
    page.
    '''
    def on_page_changed(self, page, page_num):
        print '\n--- Page', page_num+1, '\n', page.source

