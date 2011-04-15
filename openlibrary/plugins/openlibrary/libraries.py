"""Controller for /libraries.
"""
import time

import web
import couchdb

from infogami import config
from infogami.utils import delegate
from infogami.utils.view import render_template
from openlibrary.core import inlibrary

class libraries(delegate.page):
    def GET(self):
        return render_template("libraries/index")
        
class locations(delegate.page):
    path = "/libraries/locations.txt"

    def GET(self):
        libraries = inlibrary.get_libraries()
        web.header("Content-Type", "text/plain")
        return delegate.RawText(render_template("libraries/locations", libraries))
        
class stats(delegate.page):
    path = "/libraries/stats"
    
    def GET(self):
        stats  = LoanStats()
        return render_template("libraries/stats", stats);

@web.memoize
def get_admin_couchdb():
    db_url = config.get("admin", {}).get("counts_db")
    return db_url and couchdb.Database(db_url)
    
class LoanStats:
    def __init__(self):
        self.db = get_admin_couchdb()
        
    def get_loans_per_day(self):
        rows = self.db.view("loans/loans", group=True).rows
        return [[self.date2timestamp(*row.key)*1000, row.value] for row in rows]
        
    def date2timestamp(self, year, month=1, day=1):
        return time.mktime((year, month, day, 0, 0, 0, 0, 0, 0)) # time.mktime takes 9-tuple as argument
    
    def get_loan_duration_frequency(self):
        row = self.db.view("loans/duration").rows[0]
        d = {}
        for time, count in row.value['freq'].items():
            n = 1 + int(time)/24
            
            # The loan entry gets added to couch only when the loan is deleted in the database, which is probably triggered by a cron job.
            # Even though the max loan duration is 2 weeks, there is a chance that duration is more than 14.
            if n > 14: 
                n =15
            
            d[n] = d.get(n, 0) + count
        return sorted(d.items())
        
    def get_average_duration_per_month(self):
        """Returns average duration per month."""
        rows = self.db.view("loans/duration", group_level=2).rows
        return [[self.date2timestamp(*row.key)*1000, min(14, row.value['avg']/(60.0*24.0))] for row in rows]

def setup():
    pass
