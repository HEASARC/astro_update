from flask import Flask, render_template
from heasarc import astroupdate as ad
import pandas as pd
app = Flask(__name__)


@app.route("/")
def template_test():
    audef = ad.read_au_defs()
    # convert release date to a datetime object...
    audef.ad_release_date = pd.to_datetime(audef.ad_release_date, errors="coerce")
    # ... then sort by release_date
    audef.sort_values(by='ad_release_date', ascending=False, inplace=True)
    # strip out the rows without a defined release_date
    audef_for_web = audef[audef.ad_release_date.notnull()]
    return render_template('test_table.html', audef = audef_for_web )

if __name__ == '__main__':
    app.run(debug=True)