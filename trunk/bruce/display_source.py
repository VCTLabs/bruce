

class DisplaySource(object):
    def on_page_changed(self, page, page_num):
        print '*'*30, page_num+1, '*'*30
        page.print_source()
